import os

class Config:
    """Application configuration settings."""
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.environ.get('SECRET_KEY', 'queueless-bca-project-secret-key-2026')
    DATABASE = os.path.join(BASE_DIR, 'queueless.db')
    DEBUG = True
