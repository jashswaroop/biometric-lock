from app import app, db
from models import User, SystemConfig
from datetime import datetime
import os

def init_db():
    """Initialize the database with required tables and initial data."""
    with app.app_context():
        # Create all tables
        db.create_all()

        # Add default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                created_at=datetime.utcnow(),
                is_active=True
            )
            admin.set_password('Admin@123')
            db.session.add(admin)

        # Add initial system configurations
        default_configs = {
            'iris_match_threshold': '0.8',
            'min_iris_quality': '0.7',
            'max_login_attempts': '5',
            'lockout_duration_minutes': '30',
            'session_timeout_minutes': '30',
            'password_expiry_days': '90',
            'require_2fa': 'true',
            'maintenance_mode': 'false'
        }

        for key, value in default_configs.items():
            config = SystemConfig.query.filter_by(key=key).first()
            if not config:
                config = SystemConfig(
                    key=key,
                    value=value,
                    description=f'Default {key} setting',
                    updated_at=datetime.utcnow(),
                    updated_by=1  # Admin user ID
                )
                db.session.add(config)

        try:
            db.session.commit()
            print("Database initialized successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing database: {str(e)}")

def reset_db():
    """Reset the database by dropping all tables and reinitializing."""
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            print("All tables dropped successfully!")
            
            # Reinitialize database
            init_db()
        except Exception as e:
            print(f"Error resetting database: {str(e)}")

def create_test_users():
    """Create test users for development purposes."""
    with app.app_context():
        test_users = [
            {
                'username': 'test_user1',
                'email': 'test1@example.com',
                'password': 'Test@123'
            },
            {
                'username': 'test_user2',
                'email': 'test2@example.com',
                'password': 'Test@123'
            }
        ]

        try:
            for user_data in test_users:
                user = User.query.filter_by(username=user_data['username']).first()
                if not user:
                    user = User(
                        username=user_data['username'],
                        email=user_data['email'],
                        created_at=datetime.utcnow(),
                        is_active=True
                    )
                    user.set_password(user_data['password'])
                    db.session.add(user)

            db.session.commit()
            print("Test users created successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating test users: {str(e)}")

if __name__ == '__main__':
    # Check if database should be reset
    if os.getenv('RESET_DB', '').lower() == 'true':
        reset_db()
    else:
        init_db()

    # Create test users if in development environment
    if app.config['FLASK_ENV'] == 'development':
        create_test_users()