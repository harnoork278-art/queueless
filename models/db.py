import sqlite3
import os
from flask import g, current_app
from werkzeug.security import generate_password_hash

def get_db():
    """Get a database connection from application context or create a new one."""
    if 'db' not in g:
        db_path = current_app.config.get('DATABASE', 'queueless.db')
        # Ensure directory exists if path contains directories
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        # Enable foreign keys
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    """Close the database connection if open."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app=None):
    """Initialize database tables and seed initial default data."""
    if app:
        db_path = app.config.get('DATABASE', 'queueless.db')
    else:
        from config import Config
        db_path = Config.DATABASE

    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create services table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_code TEXT UNIQUE NOT NULL,
        service_name TEXT NOT NULL,
        description TEXT,
        avg_wait_per_token INTEGER NOT NULL DEFAULT 5,
        prefix TEXT NOT NULL DEFAULT 'T',
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create tokens table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token_number TEXT NOT NULL,
        service_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Waiting',
        admin_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        called_at TIMESTAMP,
        completed_at TIMESTAMP,
        cancelled_at TIMESTAMP,
        FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # Seed default Admin user if not exists
    cursor.execute("SELECT id FROM users WHERE username = ?", ('admin',))
    if not cursor.fetchone():
        admin_pass = generate_password_hash('admin123')
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, email, phone, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('admin', admin_pass, 'System Administrator', 'admin@queueless.edu', '9876543210', 'admin'))

    # Seed default Student user if not exists
    cursor.execute("SELECT id FROM users WHERE username = ?", ('student',))
    if not cursor.fetchone():
        student_pass = generate_password_hash('student123')
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, email, phone, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('student', student_pass, 'Rahul Sharma (Student)', 'rahul@student.edu', '9812345678', 'user'))

    # Seed default Services if empty
    cursor.execute("SELECT COUNT(*) as count FROM services")
    count = cursor.fetchone()[0]
    if count == 0:
        default_services = [
            ('ADM', 'Admissions & Course Counseling', 'New admissions, eligibility checks, course details & counselor queries.', 7, 'ADM', 1),
            ('ACC', 'Fee Payment & Accounts Desk', 'Tuition fee payments, dues clearance, challan verification and refunds.', 4, 'ACC', 1),
            ('DOC', 'Document Verification & Certificates', 'Bonafide certificates, marksheet verification, migration and degree certificates.', 5, 'DOC', 1),
            ('LIB', 'Library Clearance & ID Cards', 'Book return clearance, digital library access and student ID card issuing.', 3, 'LIB', 1),
            ('EXM', 'Examination & Hall Ticket Desk', 'Semester examination forms, hall ticket issues, revaluation inquiries.', 5, 'EXM', 1)
        ]
        cursor.executemany("""
            INSERT INTO services (service_code, service_name, description, avg_wait_per_token, prefix, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, default_services)

    conn.commit()
    conn.close()
