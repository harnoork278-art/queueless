from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db

class UserModel:
    """Model handling user accounts, authentication data, and roles."""

    @staticmethod
    def get_by_id(user_id):
        """Fetch user by primary key ID."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

    @staticmethod
    def get_by_username(username):
        """Fetch user by unique username (case-insensitive)."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
        return cursor.fetchone()

    @staticmethod
    def create_user(username, password, full_name, email=None, phone=None, role='user'):
        """
        Create a new user with securely hashed password.
        Returns newly created user id or raises ValueError if username is taken.
        """
        username = username.strip()
        full_name = full_name.strip()
        email = email.strip() if email else ''
        phone = phone.strip() if phone else ''

        if UserModel.get_by_username(username):
            raise ValueError(f"Username '{username}' is already registered.")

        password_hash = generate_password_hash(password)
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, email, phone, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, password_hash, full_name, email, phone, role))
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def verify_password(stored_hash, password):
        """Verify plain text password against stored hash."""
        if not stored_hash or not password:
            return False
        return check_password_hash(stored_hash, password)

    @staticmethod
    def get_all_users():
        """Retrieve list of all registered users."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, username, full_name, email, phone, role, created_at FROM users ORDER BY id DESC")
        return cursor.fetchall()
