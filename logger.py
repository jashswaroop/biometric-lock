import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class SecurityLogger:
    _instance: Optional['SecurityLogger'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SecurityLogger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Initialize the logger with proper configuration."""
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Configure main logger
        self.logger = logging.getLogger('biometric_lock')
        self.logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))

        # Prevent duplicate handlers
        if not self.logger.handlers:
            # File handler for all logs
            main_handler = logging.handlers.RotatingFileHandler(
                'logs/biometric_lock.log',
                maxBytes=10485760,  # 10MB
                backupCount=5
            )
            main_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(main_handler)

            # File handler for security events
            security_handler = logging.handlers.RotatingFileHandler(
                'logs/security_events.log',
                maxBytes=10485760,  # 10MB
                backupCount=5
            )
            security_handler.setFormatter(logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
            ))
            security_handler.setLevel(logging.WARNING)
            self.logger.addHandler(security_handler)

            # Console handler
            if os.getenv('FLASK_ENV') == 'development':
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
                self.logger.addHandler(console_handler)

    def log_auth_attempt(self, username: str, success: bool, method: str, ip_address: str):
        """Log authentication attempts."""
        status = 'SUCCESS' if success else 'FAILURE'
        self.logger.info(
            f'Authentication {status} - User: {username} - Method: {method} - IP: {ip_address}'
        )

    def log_iris_enrollment(self, username: str, success: bool, ip_address: str):
        """Log iris enrollment events."""
        status = 'SUCCESS' if success else 'FAILURE'
        self.logger.info(
            f'Iris Enrollment {status} - User: {username} - IP: {ip_address}'
        )

    def log_security_event(self, event_type: str, details: str, ip_address: str):
        """Log security-related events."""
        self.logger.warning(
            f'Security Event: {event_type} - Details: {details} - IP: {ip_address}'
        )

    def log_system_error(self, error_type: str, error_message: str, stack_trace: str = None):
        """Log system errors."""
        self.logger.error(
            f'System Error: {error_type} - Message: {error_message}'
            + (f'\nStack Trace: {stack_trace}' if stack_trace else '')
        )

    def log_rate_limit(self, ip_address: str):
        """Log rate limit violations."""
        self.logger.warning(f'Rate Limit Exceeded - IP: {ip_address}')

    def log_access_history(self, username: str, action: str, resource: str, ip_address: str):
        """Log user access history."""
        self.logger.info(
            f'Access History - User: {username} - Action: {action} '
            f'- Resource: {resource} - IP: {ip_address}'
        )

class AccessLogger:
    def __init__(self):
        self.logger = SecurityLogger()

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type:
            self.logger.log_system_error(
                error_type=exc_type.__name__,
                error_message=str(exc_val),
                stack_trace=str(exc_tb)
            )
        return False  # Don't suppress exceptions

def get_logger() -> SecurityLogger:
    """Get the singleton instance of SecurityLogger."""
    return SecurityLogger()