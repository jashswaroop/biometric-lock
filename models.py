from datetime import datetime
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from security import encrypt_iris_data, decrypt_iris_data

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for storing user account information."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    iris_data = db.Column(db.LargeBinary, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    # Relationships
    access_logs = db.relationship('AccessLog', backref='user', lazy=True)
    iris_enrollments = db.relationship('IrisEnrollment', backref='user', lazy=True)

    def set_password(self, password: str) -> None:
        """Set the user's password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the user's password."""
        return check_password_hash(self.password_hash, password)

    def set_iris_data(self, iris_data: bytes) -> None:
        """Encrypt and store iris data."""
        self.iris_data = encrypt_iris_data(iris_data)

    def get_iris_data(self) -> Optional[bytes]:
        """Retrieve and decrypt iris data."""
        if self.iris_data:
            return decrypt_iris_data(self.iris_data)
        return None

    def record_login_attempt(self, success: bool) -> None:
        """Record login attempt and update related fields."""
        if success:
            self.failed_attempts = 0
            self.last_login = datetime.utcnow()
            self.locked_until = None
        else:
            self.failed_attempts += 1
            if self.failed_attempts >= 5:
                self.locked_until = datetime.utcnow() + timedelta(minutes=30)

class IrisEnrollment(db.Model):
    """Model for tracking iris enrollment history."""
    __tablename__ = 'iris_enrollments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    quality_score = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    device_info = db.Column(db.String(256))
    operator_id = db.Column(db.Integer, nullable=True)

class AccessLog(db.Model):
    """Model for tracking system access attempts."""
    __tablename__ = 'access_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(50), nullable=False)
    success = db.Column(db.Boolean, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(256))
    auth_method = db.Column(db.String(20))
    details = db.Column(db.Text)

class SecurityEvent(db.Model):
    """Model for tracking security-related events."""
    __tablename__ = 'security_events'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolution = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)

class SystemConfig(db.Model):
    """Model for storing system configuration settings."""
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    @classmethod
    def get_setting(cls, key: str, default: str = None) -> Optional[str]:
        """Get a system configuration value."""
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default

    @classmethod
    def set_setting(cls, key: str, value: str, description: str = None,
                    updated_by: int = None) -> None:
        """Set a system configuration value."""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
            setting.updated_by = updated_by
        else:
            setting = cls(key=key, value=value, description=description,
                         updated_by=updated_by)
            db.session.add(setting)
        db.session.commit()