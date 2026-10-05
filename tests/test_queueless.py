import unittest
import os
import sys
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from config import Config
from models.db import init_db
from models.user_model import UserModel
from models.service_model import ServiceModel
from models.token_model import TokenModel

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False

class QueueLessTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        class CustomTestConfig(TestConfig):
            DATABASE = self.db_path
            
        self.app = create_app(CustomTestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_default_seeding(self):
        """Test default admin and student users are seeded."""
        admin = UserModel.get_by_username('admin')
        self.assertIsNotNone(admin)
        self.assertEqual(admin['role'], 'admin')
        self.assertTrue(UserModel.verify_password(admin['password_hash'], 'admin123'))

        student = UserModel.get_by_username('student')
        self.assertIsNotNone(student)
        self.assertEqual(student['role'], 'user')

        services = ServiceModel.get_all()
        self.assertGreaterEqual(len(services), 4)

    def test_user_registration_and_login(self):
        """Test registering a new student user and authenticating."""
        user_id = UserModel.create_user('anita', 'pass1234', 'Anita Roy', 'anita@test.com', '9876500000')
        self.assertIsNotNone(user_id)

        user = UserModel.get_by_username('anita')
        self.assertEqual(user['full_name'], 'Anita Roy')
        self.assertTrue(UserModel.verify_password(user['password_hash'], 'pass1234'))

        # Duplicate username prevention
        with self.assertRaises(ValueError):
            UserModel.create_user('anita', 'different', 'Anita Duplicate')

    def test_token_creation_and_queue_position(self):
        """Test queue issuance, sequential numbering, and position calculations."""
        # Get ADM service
        service = ServiceModel.get_by_code('ADM')
        self.assertIsNotNone(service)

        # Create two distinct users
        u1 = UserModel.create_user('user1', 'pass1', 'User One')
        u2 = UserModel.create_user('user2', 'pass2', 'User Two')

        # Token 1
        t1_id = TokenModel.create_token(service['id'], u1)
        t1_details = TokenModel.get_queue_details(t1_id)
        self.assertEqual(t1_details['status'], 'Waiting')
        self.assertEqual(t1_details['position'], 1)
        self.assertEqual(t1_details['people_ahead'], 0)

        # Token 2 for same service
        t2_id = TokenModel.create_token(service['id'], u2)
        t2_details = TokenModel.get_queue_details(t2_id)
        self.assertEqual(t2_details['status'], 'Waiting')
        self.assertEqual(t2_details['position'], 2)
        self.assertEqual(t2_details['people_ahead'], 1)

        # Duplicate active token in same service should be blocked
        with self.assertRaises(ValueError):
            TokenModel.create_token(service['id'], u1)

    def test_admin_call_next_and_complete(self):
        """Test calling next token advances queue and updates status."""
        service = ServiceModel.get_by_code('ADM')
        u1 = UserModel.create_user('u1', 'p1', 'Student 1')
        u2 = UserModel.create_user('u2', 'p2', 'Student 2')

        t1_id = TokenModel.create_token(service['id'], u1)
        t2_id = TokenModel.create_token(service['id'], u2)

        # Admin calls next
        called = TokenModel.call_next(service['id'])
        self.assertEqual(called['id'], t1_id)

        # Check t1 status is Serving
        t1_details = TokenModel.get_queue_details(t1_id)
        self.assertEqual(t1_details['status'], 'Serving')
        self.assertEqual(t1_details['position'], 0)

        # Check t2 position is now 1 in line
        t2_details = TokenModel.get_queue_details(t2_id)
        self.assertEqual(t2_details['status'], 'Waiting')
        self.assertEqual(t2_details['position'], 1)
        self.assertEqual(t2_details['current_serving'], t1_details['token']['token_number'])

        # Admin calls next again: t1 should become Completed, t2 becomes Serving
        called2 = TokenModel.call_next(service['id'])
        self.assertEqual(called2['id'], t2_id)

        t1_after = TokenModel.get_by_id(t1_id)
        self.assertEqual(t1_after['status'], 'Completed')

        t2_after = TokenModel.get_by_id(t2_id)
        self.assertEqual(t2_after['status'], 'Serving')

    def test_user_cancel_token(self):
        """Test student cancelling their own active token."""
        service = ServiceModel.get_by_code('DOC')
        user_id = UserModel.create_user('canceller', 'pass1', 'Cancel Tester')
        token_id = TokenModel.create_token(service['id'], user_id)

        # Cancel token
        res = TokenModel.cancel_token(token_id, user_id=user_id)
        self.assertTrue(res)

        token = TokenModel.get_by_id(token_id)
        self.assertEqual(token['status'], 'Cancelled')

        # Cannot cancel again
        with self.assertRaises(ValueError):
            TokenModel.cancel_token(token_id, user_id=user_id)

    def test_live_api_status_endpoint(self):
        """Test /api/token/<id>/status JSON endpoint."""
        service = ServiceModel.get_by_code('LIB')
        user_id = UserModel.create_user('apitester', 'pass123', 'API Tester')
        token_id = TokenModel.create_token(service['id'], user_id)

        # Simulate login session
        with self.client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'apitester'
            sess['role'] = 'user'

        response = self.client.get(f'/api/token/{token_id}/status')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['success'])
        self.assertEqual(json_data['status'], 'Waiting')
        self.assertEqual(json_data['token_id'], token_id)

if __name__ == '__main__':
    unittest.main()
