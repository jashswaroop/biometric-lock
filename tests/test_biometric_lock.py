import unittest
import os
import sys
import cv2
import numpy as np
from datetime import datetime, timedelta
from flask import url_for
from werkzeug.security import generate_password_hash
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import User, AccessLog, IrisEnrollment
from iris_recognition import IrisRecognition
from security import encrypt_iris_data, decrypt_iris_data

class BiometricLockTests(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            self._create_test_user()

    def tearDown(self):
        """Clean up after each test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def _create_test_user(self):
        """Create a test user for authentication tests."""
        user = User(
            username='testuser',
            email='test@example.com',
            is_active=True
        )
        user.set_password('Test@123')
        db.session.add(user)
        db.session.commit()

    def _get_test_image(self):
        """Create a test image for iris recognition tests."""
        img = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(img, (50, 50), 20, 255, -1)
        return cv2.imencode('.jpg', img)[1].tobytes()

    def test_user_registration(self):
        """Test user registration functionality."""
        response = self.app.post('/register', json={
            'username': 'newuser',
            'password': 'NewUser@123',
            'email': 'newuser@example.com'
        })
        self.assertEqual(response.status_code, 201)
        
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(user)
            self.assertTrue(user.check_password('NewUser@123'))

    def test_user_login(self):
        """Test user login with password."""
        response = self.app.post('/login', json={
            'username': 'testuser',
            'password': 'Test@123'
        })
        self.assertEqual(response.status_code, 200)

    def test_iris_enrollment(self):
        """Test iris enrollment process."""
        # Login first
        self.app.post('/login', json={
            'username': 'testuser',
            'password': 'Test@123'
        })

        # Test iris enrollment
        response = self.app.post('/capture_iris', data={
            'iris_image': (io.BytesIO(self._get_test_image()), 'test.jpg')
        })
        self.assertEqual(response.status_code, 200)

        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user.iris_data)

    def test_iris_verification(self):
        """Test iris verification process."""
        # Enroll iris first
        self.test_iris_enrollment()

        # Test verification
        response = self.app.post('/verify_iris', data={
            'iris_image': (io.BytesIO(self._get_test_image()), 'test.jpg')
        })
        self.assertEqual(response.status_code, 200)

    def test_failed_login_lockout(self):
        """Test account lockout after multiple failed attempts."""
        for _ in range(5):
            response = self.app.post('/login', json={
                'username': 'testuser',
                'password': 'WrongPassword'
            })

        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            self.assertIsNotNone(user.locked_until)
            self.assertTrue(user.locked_until > datetime.utcnow())

    def test_access_logging(self):
        """Test access attempt logging."""
        self.app.post('/login', json={
            'username': 'testuser',
            'password': 'Test@123'
        })

        with app.app_context():
            log = AccessLog.query.filter_by(user_id=1).first()
            self.assertIsNotNone(log)
            self.assertTrue(log.success)

    def test_iris_data_encryption(self):
        """Test iris data encryption and decryption."""
        test_data = b'test_iris_data'
        encrypted = encrypt_iris_data(test_data)
        decrypted = decrypt_iris_data(encrypted)
        self.assertEqual(test_data, decrypted)

    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        for _ in range(10):
            response = self.app.post('/verify_iris', data={
                'iris_image': (io.BytesIO(self._get_test_image()), 'test.jpg')
            })
            if response.status_code == 429:
                break
        self.assertEqual(response.status_code, 429)

    def test_iris_quality_check(self):
        """Test iris image quality assessment."""
        iris_recognition = IrisRecognition()
        test_image = self._get_test_image()
        quality_score = iris_recognition.process_image(test_image)
        self.assertIsNotNone(quality_score)

    def test_session_management(self):
        """Test session management and timeout."""
        # Login
        self.app.post('/login', json={
            'username': 'testuser',
            'password': 'Test@123'
        })

        # Access protected route
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

        # Test session timeout
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=1)
        import time
        time.sleep(2)
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

if __name__ == '__main__':
    unittest.main()