import sqlite3
from datetime import datetime
from .db import get_db
from .service_model import ServiceModel

class TokenModel:
    """Model managing queue tokens, positions, wait calculations, and lifecycle statuses."""

    @staticmethod
    def get_by_id(token_id):
        """Retrieve token with joined service and user information."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                t.*,
                s.service_code,
                s.service_name,
                s.avg_wait_per_token,
                s.prefix,
                u.username,
                u.full_name,
                u.email,
                u.phone
            FROM tokens t
            JOIN services s ON t.service_id = s.id
            JOIN users u ON t.user_id = u.id
            WHERE t.id = ?
        """, (token_id,))
        return cursor.fetchone()

    @staticmethod
    def get_active_token_for_user(user_id, service_id=None):
        """Check if user has an active token (Waiting or Serving), optionally for a specific service."""
        db = get_db()
        cursor = db.cursor()
        if service_id:
            cursor.execute("""
                SELECT * FROM tokens
                WHERE user_id = ? AND service_id = ? AND status IN ('Waiting', 'Serving')
                ORDER BY id DESC LIMIT 1
            """, (user_id, service_id))
        else:
            cursor.execute("""
                SELECT * FROM tokens
                WHERE user_id = ? AND status IN ('Waiting', 'Serving')
                ORDER BY id DESC LIMIT 1
            """, (user_id,))
        return cursor.fetchone()

    @staticmethod
    def generate_token_number(service_id):
        """Generate next sequential token number for service, e.g. ADM-101, ADM-102."""
        service = ServiceModel.get_by_id(service_id)
        if not service:
            raise ValueError("Service not found")

        prefix = service['prefix'] or service['service_code']
        db = get_db()
        cursor = db.cursor()
        
        # Look for the last token issued for this service
        cursor.execute("""
            SELECT token_number FROM tokens
            WHERE service_id = ?
            ORDER BY id DESC LIMIT 1
        """, (service_id,))
        last_row = cursor.fetchone()

        if last_row and last_row['token_number']:
            try:
                # Extract number part after prefix-
                last_num = int(last_row['token_number'].split('-')[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 101
        else:
            next_num = 101

        return f"{prefix}-{next_num}"

    @staticmethod
    def create_token(service_id, user_id):
        """Issue a new token for a user in a specified service."""
        service = ServiceModel.get_by_id(service_id)
        if not service or not service['is_active']:
            raise ValueError("The selected service is currently unavailable or inactive.")

        # Check for existing active token in this service
        active = TokenModel.get_active_token_for_user(user_id, service_id)
        if active:
            raise ValueError(
                f"You already hold an active token ({active['token_number']}) for {service['service_name']}."
            )

        token_number = TokenModel.generate_token_number(service_id)
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO tokens (token_number, service_id, user_id, status)
            VALUES (?, ?, ?, 'Waiting')
        """, (token_number, service_id, user_id))
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_queue_details(token_id):
        """Calculate live queue position, people ahead, currently serving, and estimated wait."""
        token = TokenModel.get_by_id(token_id)
        if not token:
            return None

        db = get_db()
        cursor = db.cursor()

        # Find currently serving token for this service
        cursor.execute("""
            SELECT token_number FROM tokens
            WHERE service_id = ? AND status = 'Serving'
            ORDER BY called_at DESC LIMIT 1
        """, (token['service_id'],))
        current_serving_row = cursor.fetchone()
        current_serving = current_serving_row['token_number'] if current_serving_row else "None (Waiting for Next)"

        if token['status'] == 'Serving':
            return {
                'token': token,
                'status': 'Serving',
                'position': 0,
                'position_label': 'Currently Serving',
                'people_ahead': 0,
                'estimated_wait_minutes': 0,
                'estimated_wait_text': 'You are currently being served!',
                'current_serving': current_serving
            }
        elif token['status'] == 'Waiting':
            # Count how many waiting tokens are ahead
            cursor.execute("""
                SELECT COUNT(*) FROM tokens
                WHERE service_id = ? AND status = 'Waiting' AND id < ?
            """, (token['service_id'], token['id']))
            people_ahead = cursor.fetchone()[0]
            position = people_ahead + 1

            # Estimate wait time
            has_active_counter = 1 if current_serving_row else 0
            avg_wait = token['avg_wait_per_token'] or 5
            total_minutes = (people_ahead + has_active_counter) * avg_wait

            if total_minutes <= 0:
                wait_text = "Less than 2 mins (Next in line)"
            elif total_minutes < 60:
                wait_text = f"~{total_minutes} mins"
            else:
                hrs = total_minutes // 60
                mins = total_minutes % 60
                wait_text = f"~{hrs} hr {mins} mins" if mins else f"~{hrs} hrs"

            return {
                'token': token,
                'status': 'Waiting',
                'position': position,
                'position_label': f"#{position} in queue",
                'people_ahead': people_ahead,
                'estimated_wait_minutes': total_minutes,
                'estimated_wait_text': wait_text,
                'current_serving': current_serving
            }
        else:
            # Completed or Cancelled
            return {
                'token': token,
                'status': token['status'],
                'position': None,
                'position_label': token['status'],
                'people_ahead': 0,
                'estimated_wait_minutes': 0,
                'estimated_wait_text': f"Token is {token['status']}",
                'current_serving': current_serving
            }

    @staticmethod
    def get_user_tokens(user_id):
        """Retrieve all tokens for a user, active first, then newest."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                t.*,
                s.service_code,
                s.service_name,
                s.avg_wait_per_token
            FROM tokens t
            JOIN services s ON t.service_id = s.id
            WHERE t.user_id = ?
            ORDER BY 
                CASE 
                    WHEN t.status = 'Serving' THEN 1
                    WHEN t.status = 'Waiting' THEN 2
                    ELSE 3
                END,
                t.id DESC
        """, (user_id,))
        return cursor.fetchall()

    @staticmethod
    def cancel_token(token_id, user_id=None, notes=None):
        """Cancel a token. If user_id is provided, verify ownership."""
        db = get_db()
        cursor = db.cursor()
        if user_id:
            cursor.execute("SELECT * FROM tokens WHERE id = ? AND user_id = ?", (token_id, user_id))
        else:
            cursor.execute("SELECT * FROM tokens WHERE id = ?", (token_id,))
        
        token = cursor.fetchone()
        if not token:
            raise ValueError("Token not found or unauthorized.")

        if token['status'] not in ('Waiting', 'Serving'):
            raise ValueError(f"Cannot cancel a token that is already {token['status']}.")

        cursor.execute("""
            UPDATE tokens
            SET status = 'Cancelled', cancelled_at = CURRENT_TIMESTAMP, admin_notes = ?
            WHERE id = ?
        """, (notes or 'Cancelled by user', token_id))
        db.commit()
        return True

    @staticmethod
    def call_next(service_id):
        """
        Admin calls the next waiting token for a service:
        - Automatically completes any currently 'Serving' token for this service
        - Finds oldest 'Waiting' token and changes status to 'Serving'
        """
        db = get_db()
        cursor = db.cursor()

        # Complete currently serving token for this service if any
        cursor.execute("""
            UPDATE tokens 
            SET status = 'Completed', completed_at = CURRENT_TIMESTAMP
            WHERE service_id = ? AND status = 'Serving'
        """, (service_id,))

        # Find next waiting token
        cursor.execute("""
            SELECT id, token_number FROM tokens
            WHERE service_id = ? AND status = 'Waiting'
            ORDER BY id ASC LIMIT 1
        """, (service_id,))
        next_token = cursor.fetchone()

        if not next_token:
            db.commit()
            return None

        # Set status to Serving
        cursor.execute("""
            UPDATE tokens
            SET status = 'Serving', called_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (next_token['id'],))
        db.commit()
        return next_token

    @staticmethod
    def update_status(token_id, new_status, notes=None):
        """Admin updates token status to 'Completed' or 'Cancelled' or 'Serving'."""
        if new_status not in ('Waiting', 'Serving', 'Completed', 'Cancelled'):
            raise ValueError(f"Invalid status: {new_status}")

        db = get_db()
        cursor = db.cursor()
        
        if new_status == 'Completed':
            cursor.execute("""
                UPDATE tokens
                SET status = 'Completed', completed_at = CURRENT_TIMESTAMP, admin_notes = COALESCE(?, admin_notes)
                WHERE id = ?
            """, (notes, token_id))
        elif new_status == 'Cancelled':
            cursor.execute("""
                UPDATE tokens
                SET status = 'Cancelled', cancelled_at = CURRENT_TIMESTAMP, admin_notes = COALESCE(?, admin_notes)
                WHERE id = ?
            """, (notes or 'Cancelled by admin', token_id))
        elif new_status == 'Serving':
            # Also complete any other serving token in this service
            cursor.execute("SELECT service_id FROM tokens WHERE id = ?", (token_id,))
            s_row = cursor.fetchone()
            if s_row:
                cursor.execute("""
                    UPDATE tokens SET status = 'Completed', completed_at = CURRENT_TIMESTAMP
                    WHERE service_id = ? AND status = 'Serving' AND id != ?
                """, (s_row['service_id'], token_id))
            cursor.execute("""
                UPDATE tokens
                SET status = 'Serving', called_at = CURRENT_TIMESTAMP, admin_notes = COALESCE(?, admin_notes)
                WHERE id = ?
            """, (notes, token_id))

        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def get_service_queue(service_id=None, status_filter=None, limit=50):
        """Get list of tokens for admin queue table."""
        db = get_db()
        cursor = db.cursor()
        
        query = """
            SELECT 
                t.*,
                s.service_code,
                s.service_name,
                u.username,
                u.full_name,
                u.phone
            FROM tokens t
            JOIN services s ON t.service_id = s.id
            JOIN users u ON t.user_id = u.id
            WHERE 1=1
        """
        params = []
        if service_id:
            query += " AND t.service_id = ?"
            params.append(service_id)
        if status_filter:
            query += " AND t.status = ?"
            params.append(status_filter)

        query += """
            ORDER BY 
                CASE 
                    WHEN t.status = 'Serving' THEN 1
                    WHEN t.status = 'Waiting' THEN 2
                    ELSE 3
                END,
                t.id DESC
            LIMIT ?
        """
        params.append(limit)
        cursor.execute(query, params)
        return cursor.fetchall()

    @staticmethod
    def get_admin_stats():
        """Retrieve aggregated statistics for the admin overview dashboard."""
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT COUNT(*) FROM tokens WHERE status = 'Waiting'")
        total_waiting = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tokens WHERE status = 'Serving'")
        total_serving = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tokens WHERE status = 'Completed'")
        total_completed = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tokens WHERE status = 'Cancelled'")
        total_cancelled = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tokens")
        total_all_time = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM services WHERE is_active = 1")
        active_services = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
        total_users = cursor.fetchone()[0]

        return {
            'total_waiting': total_waiting,
            'total_serving': total_serving,
            'total_completed': total_completed,
            'total_cancelled': total_cancelled,
            'total_all_time': total_all_time,
            'active_services': active_services,
            'total_users': total_users
        }
