from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
from typing import Dict, Callable, Any
import jwt
import redis
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Redis for rate limiting
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
except:
    print("Warning: Redis not available, falling back to in-memory storage")
    redis_client = None

# In-memory storage fallback
rate_limit_storage: Dict[str, Dict[str, Any]] = {}

def get_rate_limit_key(ip: str) -> str:
    """Generate a rate limit key for Redis."""
    return f"rate_limit:{ip}"

def is_rate_limited(ip: str) -> bool:
    """Check if the IP is rate limited."""
    window = int(os.getenv('RATE_LIMIT_WINDOW', 3600))  # 1 hour default
    max_attempts = int(os.getenv('MAX_ATTEMPTS', 5))
    
    if redis_client:
        key = get_rate_limit_key(ip)
        attempts = redis_client.get(key)
        
        if attempts is None:
            redis_client.setex(key, window, 1)
            return False
        
        attempts = int(attempts)
        if attempts >= max_attempts:
            return True
        
        redis_client.incr(key)
        return False
    else:
        # Fallback to in-memory storage
        now = datetime.now()
        if ip in rate_limit_storage:
            data = rate_limit_storage[ip]
            if now - data['start_time'] > timedelta(seconds=window):
                rate_limit_storage[ip] = {'attempts': 1, 'start_time': now}
                return False
            
            if data['attempts'] >= max_attempts:
                return True
            
            data['attempts'] += 1
            return False
        else:
            rate_limit_storage[ip] = {'attempts': 1, 'start_time': now}
            return False

def rate_limit(f: Callable) -> Callable:
    """Decorator to apply rate limiting to routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        
        if is_rate_limited(ip):
            return jsonify({
                'error': 'Too many attempts. Please try again later.',
                'retry_after': int(os.getenv('RATE_LIMIT_WINDOW', 3600))
            }), 429
        
        return f(*args, **kwargs)
    
    return decorated_function

def generate_token(user_id: int) -> str:
    """Generate a JWT token for the user."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow()
    }
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def verify_token(token: str) -> Dict:
    """Verify a JWT token and return the payload."""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')

def encrypt_iris_data(iris_data: bytes) -> bytes:
    """Encrypt iris data before storage.
    
    This is a placeholder for actual encryption implementation.
    In a production environment, use strong encryption methods.
    """
    # TODO: Implement proper encryption
    return iris_data

def decrypt_iris_data(encrypted_data: bytes) -> bytes:
    """Decrypt iris data for verification.
    
    This is a placeholder for actual decryption implementation.
    In a production environment, use strong decryption methods.
    """
    # TODO: Implement proper decryption
    return encrypted_data

def sanitize_input(data: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks."""
    # Remove potentially dangerous characters and patterns
    # This is a basic implementation - enhance based on requirements
    dangerous_chars = ['<', '>', '"', "'", ';', '--']
    sanitized = data
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    return sanitized

def validate_password_strength(password: str) -> bool:
    """Validate password strength."""
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    return has_upper and has_lower and has_digit and has_special

def secure_headers() -> Dict[str, str]:
    """Return security headers for HTTP responses."""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }