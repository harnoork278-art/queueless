from .db import get_db

class ServiceModel:
    """Model managing service counters and queue configurations."""

    @staticmethod
    def get_all(active_only=False):
        """Retrieve all services, optionally filtering for active only."""
        db = get_db()
        cursor = db.cursor()
        if active_only:
            cursor.execute("SELECT * FROM services WHERE is_active = 1 ORDER BY service_name ASC")
        else:
            cursor.execute("SELECT * FROM services ORDER BY id ASC")
        return cursor.fetchall()

    @staticmethod
    def get_by_id(service_id):
        """Retrieve service by its ID."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,))
        return cursor.fetchone()

    @staticmethod
    def get_by_code(service_code):
        """Retrieve service by unique code (e.g. ADM, ACC)."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM services WHERE UPPER(service_code) = UPPER(?)", (service_code.strip(),))
        return cursor.fetchone()

    @staticmethod
    def create(service_code, service_name, description, avg_wait_per_token=5, prefix=None):
        """Create a new service counter."""
        service_code = service_code.strip().upper()
        service_name = service_name.strip()
        prefix = (prefix or service_code[:4]).strip().upper()
        avg_wait = int(avg_wait_per_token) if avg_wait_per_token else 5

        if ServiceModel.get_by_code(service_code):
            raise ValueError(f"Service code '{service_code}' already exists.")

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO services (service_code, service_name, description, avg_wait_per_token, prefix, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (service_code, service_name, description, avg_wait, prefix))
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def update(service_id, service_name, description, avg_wait_per_token, prefix):
        """Update service details."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            UPDATE services
            SET service_name = ?, description = ?, avg_wait_per_token = ?, prefix = ?
            WHERE id = ?
        """, (service_name.strip(), description.strip(), int(avg_wait_per_token), prefix.strip().upper(), service_id))
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def toggle_status(service_id):
        """Toggle service active/inactive status."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT is_active FROM services WHERE id = ?", (service_id,))
        row = cursor.fetchone()
        if not row:
            return False
        new_status = 0 if row['is_active'] == 1 else 1
        cursor.execute("UPDATE services SET is_active = ? WHERE id = ?", (new_status, service_id))
        db.commit()
        return new_status

    @staticmethod
    def delete(service_id):
        """Delete service counter if it has no tokens, or deactivate."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM tokens WHERE service_id = ?", (service_id,))
        token_count = cursor.fetchone()[0]
        if token_count > 0:
            # Has tokens, cannot hard delete: deactivate instead
            cursor.execute("UPDATE services SET is_active = 0 WHERE id = ?", (service_id,))
            db.commit()
            return False
        else:
            cursor.execute("DELETE FROM services WHERE id = ?", (service_id,))
            db.commit()
            return True

    @staticmethod
    def get_services_with_metrics():
        """Retrieve all services with live metrics: currently serving, waiting count, completed count."""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT 
                s.id,
                s.service_code,
                s.service_name,
                s.description,
                s.avg_wait_per_token,
                s.prefix,
                s.is_active,
                (SELECT COUNT(*) FROM tokens t WHERE t.service_id = s.id AND t.status = 'Waiting') AS waiting_count,
                (SELECT t2.token_number FROM tokens t2 WHERE t2.service_id = s.id AND t2.status = 'Serving' ORDER BY t2.called_at DESC LIMIT 1) AS current_serving,
                (SELECT COUNT(*) FROM tokens t3 WHERE t3.service_id = s.id AND t3.status = 'Completed') AS completed_count
            FROM services s
            ORDER BY s.id ASC
        """)
        return cursor.fetchall()
