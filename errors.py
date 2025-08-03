from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from logger import get_logger

logger = get_logger()

class BiometricError(Exception):
    """Base exception class for biometric lock system."""
    def __init__(self, message: str, status_code: int = 400, payload: Optional[Dict] = None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        rv = dict(self.payload or {})
        rv['error'] = True
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        rv['timestamp'] = datetime.utcnow().isoformat()
        return rv

class IrisRecognitionError(BiometricError):
    """Exception raised for errors in iris recognition process."""
    def __init__(self, message: str = 'Iris recognition failed', status_code: int = 400,
                 payload: Optional[Dict] = None):
        super().__init__(message, status_code, payload)

class AuthenticationError(BiometricError):
    """Exception raised for authentication failures."""
    def __init__(self, message: str = 'Authentication failed', status_code: int = 401,
                 payload: Optional[Dict] = None):
        super().__init__(message, status_code, payload)

class RateLimitError(BiometricError):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, message: str = 'Rate limit exceeded', status_code: int = 429,
                 payload: Optional[Dict] = None):
        super().__init__(message, status_code, payload)

class ValidationError(BiometricError):
    """Exception raised for validation errors."""
    def __init__(self, message: str = 'Validation failed', status_code: int = 400,
                 payload: Optional[Dict] = None):
        super().__init__(message, status_code, payload)

class DatabaseError(BiometricError):
    """Exception raised for database operation errors."""
    def __init__(self, message: str = 'Database operation failed', status_code: int = 500,
                 payload: Optional[Dict] = None):
        super().__init__(message, status_code, payload)

class ConfigurationError(BiometricError):
    """Exception raised for configuration errors."""
    def __init__(self, message: str = 'Configuration error', status_code: int = 500,
                 payload: Optional[Dict] = None):
        super().__init__(message, status_code, payload)

def handle_error_response(error: Exception) -> Tuple[Dict[str, Any], int]:
    """Handle error responses in a consistent format."""
    if isinstance(error, BiometricError):
        response = error.to_dict()
        status_code = error.status_code
    else:
        response = {
            'error': True,
            'message': str(error),
            'status_code': 500,
            'timestamp': datetime.utcnow().isoformat()
        }
        status_code = 500

    # Log the error
    logger.log_system_error(
        error_type=error.__class__.__name__,
        error_message=str(error)
    )

    return response, status_code

def register_error_handlers(app):
    """Register error handlers for the Flask application."""
    
    @app.errorhandler(BiometricError)
    def handle_biometric_error(error):
        response, status_code = handle_error_response(error)
        return jsonify(response), status_code

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'error': True,
            'message': 'Resource not found',
            'status_code': 404,
            'timestamp': datetime.utcnow().isoformat()
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': True,
            'message': 'Internal server error',
            'status_code': 500,
            'timestamp': datetime.utcnow().isoformat()
        }), 500

    @app.errorhandler(429)
    def ratelimit_error(error):
        return jsonify({
            'error': True,
            'message': 'Too many requests',
            'status_code': 429,
            'timestamp': datetime.utcnow().isoformat()
        }), 429

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        response, status_code = handle_error_response(error)
        return jsonify(response), status_code