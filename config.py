import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
    FLASK_APP = os.getenv('FLASK_APP', 'app.py')
    
    # Database Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///biometric.db')
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.urandom(24)
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '100/hour'
    RATELIMIT_HEADERS_ENABLED = True
    
    # Iris Recognition Settings
    IRIS_MATCH_THRESHOLD = float(os.getenv('IRIS_MATCH_THRESHOLD', 0.8))
    MIN_IRIS_QUALITY = float(os.getenv('MIN_IRIS_QUALITY', 0.7))
    
    # Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    FLASK_ENV = 'development'
    SESSION_COOKIE_SECURE = False
    
    # Development Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///biometric_dev.db'
    
    # Development Logging
    LOG_LEVEL = 'DEBUG'
    
    # Mail Settings for Development
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    FLASK_ENV = 'testing'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost'
    
    # Test Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    FLASK_ENV = 'production'
    
    # Production Security Settings
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # Production Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Production Logging
    LOG_LEVEL = 'INFO'
    
    # SSL/TLS Configuration
    SSL_REDIRECT = True
    
    # Production Mail Settings
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    
    @classmethod
    def init_app(cls, app):
        """Production-specific initialization."""
        # Log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.INFO)
        app.logger.addHandler(syslog_handler)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}