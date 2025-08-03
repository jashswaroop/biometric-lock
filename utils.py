import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
from PIL import Image
import io
import json
import base64
from logger import get_logger
from models import User, AccessLog, SecurityEvent
from flask import current_app

logger = get_logger()

def process_image_upload(image_data: bytes) -> Optional[np.ndarray]:
    """Process uploaded image data into OpenCV format."""
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        # Decode the image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        logger.log_system_error('Image Processing Error', str(e))
        return None

def enhance_iris_image(image: np.ndarray) -> Optional[np.ndarray]:
    """Enhance iris image quality for better recognition."""
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization
        equalized = cv2.equalizeHist(gray)
        
        # Apply adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(equalized)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        
        return blurred
    except Exception as e:
        logger.log_system_error('Image Enhancement Error', str(e))
        return None

def calculate_iris_quality_score(image: np.ndarray) -> float:
    """Calculate quality score for iris image."""
    try:
        # Convert to grayscale if not already
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Calculate image statistics
        mean_intensity = np.mean(gray)
        std_intensity = np.std(gray)
        
        # Calculate image sharpness
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normalize scores
        intensity_score = min(mean_intensity / 127.5, 1.0)
        contrast_score = min(std_intensity / 64.0, 1.0)
        sharpness_score = min(laplacian_var / 500.0, 1.0)
        
        # Weighted average of scores
        quality_score = (
            0.3 * intensity_score +
            0.3 * contrast_score +
            0.4 * sharpness_score
        )
        
        return quality_score
    except Exception as e:
        logger.log_system_error('Quality Score Calculation Error', str(e))
        return 0.0

def log_access_attempt(user: User, success: bool, auth_method: str,
                      ip_address: str, user_agent: str) -> None:
    """Log an access attempt to the database."""
    try:
        access_log = AccessLog(
            user_id=user.id,
            success=success,
            action='login',
            ip_address=ip_address,
            user_agent=user_agent,
            auth_method=auth_method
        )
        current_app.db.session.add(access_log)
        current_app.db.session.commit()
        
        # Update user's login attempt record
        user.record_login_attempt(success)
        current_app.db.session.commit()
        
        # Log security event if necessary
        if not success:
            log_security_event(
                'failed_login',
                f'Failed login attempt for user {user.username}',
                'warning',
                ip_address,
                user.id
            )
    except Exception as e:
        logger.log_system_error('Access Log Error', str(e))

def log_security_event(event_type: str, description: str, severity: str,
                      ip_address: str, user_id: Optional[int] = None) -> None:
    """Log a security event to the database."""
    try:
        security_event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            ip_address=ip_address,
            user_id=user_id
        )
        current_app.db.session.add(security_event)
        current_app.db.session.commit()
    except Exception as e:
        logger.log_system_error('Security Event Log Error', str(e))

def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_client_info(request) -> Tuple[str, str]:
    """Extract client IP address and user agent from request."""
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    return ip_address, user_agent

def create_error_response(message: str, status_code: int = 400) -> Tuple[Dict[str, Any], int]:
    """Create standardized error response."""
    return {
        'error': True,
        'message': message,
        'timestamp': format_datetime(datetime.utcnow())
    }, status_code

def create_success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
    """Create standardized success response."""
    response = {
        'error': False,
        'timestamp': format_datetime(datetime.utcnow())
    }
    if data is not None:
        response['data'] = data
    if message is not None:
        response['message'] = message
    return response

def encode_image_to_base64(image: np.ndarray) -> str:
    """Convert OpenCV image to base64 string."""
    try:
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')
    except Exception as e:
        logger.log_system_error('Image Encoding Error', str(e))
        return ''

def decode_base64_to_image(base64_string: str) -> Optional[np.ndarray]:
    """Convert base64 string to OpenCV image."""
    try:
        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        logger.log_system_error('Image Decoding Error', str(e))
        return None