"""
Database initialization and reset script for QueueLess Virtual Queue System.
Run: python init_db.py
"""
import os
import sys
from models.db import init_db
from config import Config

def main():
    print("=" * 60)
    print(" QueueLess – Database Initialization & Seeding")
    print("=" * 60)
    print(f"Target Database File: {Config.DATABASE}")
    
    init_db()
    
    print("\n[OK] Database initialized successfully!")
    print("\nDefault Pre-seeded Accounts:")
    print("  1. Administrator:")
    print("     - Username: admin")
    print("     - Password: admin123")
    print("     - Role:     admin")
    print("\n  2. Student / User:")
    print("     - Username: student")
    print("     - Password: student123")
    print("     - Role:     user")
    print("\nPre-seeded Services:")
    print("  - ADM: Admissions & Course Counseling")
    print("  - ACC: Fee Payment & Accounts Desk")
    print("  - DOC: Document Verification & Certificates")
    print("  - LIB: Library Clearance & ID Cards")
    print("  - EXM: Examination & Hall Ticket Desk")
    print("=" * 60)

if __name__ == '__main__':
    main()
