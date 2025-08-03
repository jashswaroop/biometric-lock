#!/usr/bin/env python
import click
import os
import sys
from flask.cli import FlaskGroup
from app import app, db
from models import User, SystemConfig
from datetime import datetime
from werkzeug.security import generate_password_hash

cli = FlaskGroup(app)

@cli.command('init-db')
def init_db():
    """Initialize the database."""
    click.echo('Initializing the database...')
    db.create_all()
    click.echo('Database initialized successfully!')

@cli.command('create-admin')
@click.option('--username', prompt=True, help='Admin username')
@click.option('--email', prompt=True, help='Admin email')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
def create_admin(username, email, password):
    """Create an admin user."""
    try:
        user = User(
            username=username,
            email=email,
            is_active=True,
            created_at=datetime.utcnow()
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'Admin user {username} created successfully!')
    except Exception as e:
        click.echo(f'Error creating admin user: {str(e)}')
        db.session.rollback()

@cli.command('reset-password')
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='New password')
def reset_password(username, password):
    """Reset a user's password."""
    try:
        user = User.query.filter_by(username=username).first()
        if user:
            user.set_password(password)
            db.session.commit()
            click.echo(f'Password reset successful for user {username}')
        else:
            click.echo(f'User {username} not found')
    except Exception as e:
        click.echo(f'Error resetting password: {str(e)}')
        db.session.rollback()

@cli.command('list-users')
def list_users():
    """List all users in the system."""
    users = User.query.all()
    if users:
        click.echo('Registered users:')
        for user in users:
            click.echo(f'Username: {user.username}, Email: {user.email}, Active: {user.is_active}')
    else:
        click.echo('No users found')

@cli.command('update-config')
@click.option('--key', prompt=True, help='Configuration key')
@click.option('--value', prompt=True, help='Configuration value')
def update_config(key, value):
    """Update system configuration."""
    try:
        config = SystemConfig.query.filter_by(key=key).first()
        if config:
            config.value = value
            config.updated_at = datetime.utcnow()
            db.session.commit()
            click.echo(f'Configuration {key} updated successfully')
        else:
            click.echo(f'Configuration key {key} not found')
    except Exception as e:
        click.echo(f'Error updating configuration: {str(e)}')
        db.session.rollback()

@cli.command('backup-db')
@click.option('--output', default='backup.sql', help='Output file name')
def backup_db(output):
    """Backup the database."""
    try:
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            import shutil
            db_file = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            shutil.copy2(db_file, output)
            click.echo(f'Database backed up to {output}')
        else:
            click.echo('Backup only supported for SQLite databases')
    except Exception as e:
        click.echo(f'Error backing up database: {str(e)}')

@cli.command('clean-logs')
@click.option('--days', default=30, help='Delete logs older than specified days')
def clean_logs(days):
    """Clean old log entries."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        from models import AccessLog, SecurityEvent
        
        # Clean access logs
        deleted_access = AccessLog.query.filter(AccessLog.timestamp < cutoff_date).delete()
        
        # Clean security events
        deleted_events = SecurityEvent.query.filter(SecurityEvent.timestamp < cutoff_date).delete()
        
        db.session.commit()
        click.echo(f'Cleaned {deleted_access} access logs and {deleted_events} security events')
    except Exception as e:
        click.echo(f'Error cleaning logs: {str(e)}')
        db.session.rollback()

@cli.command('check-system')
def check_system():
    """Check system health and configuration."""
    click.echo('Checking system status...')
    
    # Check database connection
    try:
        db.session.execute('SELECT 1')
        click.echo('✓ Database connection: OK')
    except Exception as e:
        click.echo(f'✗ Database connection: ERROR - {str(e)}')
    
    # Check configuration
    try:
        configs = SystemConfig.query.all()
        click.echo(f'✓ System configurations: {len(configs)} entries found')
    except Exception as e:
        click.echo(f'✗ System configurations: ERROR - {str(e)}')
    
    # Check file permissions
    upload_dir = os.path.join(app.root_path, 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    if os.access(upload_dir, os.W_OK):
        click.echo('✓ Upload directory: Writable')
    else:
        click.echo('✗ Upload directory: Not writable')

if __name__ == '__main__':
    cli()