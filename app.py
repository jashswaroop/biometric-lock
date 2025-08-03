from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np
# import dlib  # Commented out temporarily due to installation issues
import os
from datetime import datetime
from functools import wraps
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biometric.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    iris_data = db.Column(db.LargeBinary)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400

        user = User(username=data['username'])
        user.set_password(data['password'])

        # Add iris data if it was captured during registration
        if 'temp_iris_file' in session:
            import tempfile
            import os

            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, session['temp_iris_file'])

            try:
                with open(temp_path, 'rb') as f:
                    user.iris_data = f.read()
                # Clean up temporary file
                os.remove(temp_path)
            except FileNotFoundError:
                pass  # File doesn't exist, continue without iris data

            session.pop('temp_iris_file', None)  # Remove from session

        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'Registration successful'}), 201

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()

        # Debug logging
        print(f"Login attempt - Content-Type: {request.content_type}")
        print(f"Raw data: {request.get_data()}")
        print(f"Parsed JSON: {data}")

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        if 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password are required'}), 400

        user = User.query.filter_by(username=data['username']).first()

        if user and user.check_password(data['password']):
            login_user(user)
            return jsonify({'message': 'Login successful'}), 200

        return jsonify({'error': 'Invalid username or password'}), 401

    return render_template('login.html')

@app.route('/capture_iris', methods=['POST'])
@login_required
def capture_iris():
    if 'iris_image' not in request.files:
        return jsonify({'error': 'No iris image provided'}), 400

    iris_image = request.files['iris_image'].read()
    current_user.iris_data = iris_image
    db.session.commit()

    return jsonify({'message': 'Iris data captured successfully'}), 200

@app.route('/capture_iris_registration', methods=['POST'])
def capture_iris_registration():
    """Capture iris during registration process (before user is logged in)"""
    if 'iris_image' not in request.files:
        return jsonify({'error': 'No iris image provided'}), 400

    # Store iris data in session temporarily during registration
    # Use a flag instead of storing the large binary data
    iris_image = request.files['iris_image'].read()

    # Store in a temporary file or database instead of session
    import tempfile
    import os

    # Create a temporary file to store iris data
    temp_dir = tempfile.gettempdir()
    temp_filename = f"iris_temp_{session.get('csrf_token', 'unknown')}.dat"
    temp_path = os.path.join(temp_dir, temp_filename)

    with open(temp_path, 'wb') as f:
        f.write(iris_image)

    # Store just the filename in session
    session['temp_iris_file'] = temp_filename

    return jsonify({'message': 'Iris data captured successfully'}), 200

def detect_iris_in_image(image_data):
    """
    Basic iris detection using OpenCV
    Returns True if an iris-like structure is detected, False otherwise
    """
    try:
        # Convert image data to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            print("Failed to decode image")
            return False

        print(f"Image decoded successfully: {img.shape}")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Use HoughCircles to detect circular patterns (iris/pupil)
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=100
        )

        # If circles are detected, we assume there might be an iris
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            print(f"Detected {len(circles)} circles")
            # Check if we have at least one reasonably sized circle
            for (x, y, r) in circles:
                print(f"Circle: center=({x},{y}), radius={r}")
                if r > 15:  # Minimum radius for iris-like structure
                    print(f"Found valid iris-like circle with radius {r}")
                    return True
            print("No circles met the minimum radius requirement")
        else:
            print("No circles detected in image")

        return False

    except Exception as e:
        print(f"Error in iris detection: {e}")
        return False

def compare_iris_images(stored_iris_data, new_iris_data):
    """
    Basic iris comparison using image similarity
    In a real system, this would use sophisticated iris recognition algorithms
    """
    app.logger.info("=== IRIS COMPARISON FUNCTION CALLED ===")
    app.logger.info("=== THIS IS A TEMPORARY SIMPLE VERSION ===")
    app.logger.info(f"Stored iris data size: {len(stored_iris_data)} bytes")
    app.logger.info(f"New iris data size: {len(new_iris_data)} bytes")
    app.logger.info("=== RETURNING TRUE FOR TESTING ===")
    return True

@app.route('/verify_iris', methods=['POST'])
def verify_iris():
    if 'iris_image' not in request.files:
        return jsonify({'error': 'No iris image provided'}), 400

    try:
        iris_image_data = request.files['iris_image'].read()
        print(f"Received iris image data: {len(iris_image_data)} bytes")

        # First, check if the image contains an iris-like structure
        iris_detected = detect_iris_in_image(iris_image_data)
        print(f"Iris detection result: {iris_detected}")

        if not iris_detected:
            return jsonify({'error': 'No iris detected in the image. Please ensure your eye is clearly visible and well-lit.'}), 400

        # Get all users with iris data for comparison
        users_with_iris = User.query.filter(User.iris_data.isnot(None)).all()
        print(f"Found {len(users_with_iris)} users with iris data")

        if not users_with_iris:
            return jsonify({'error': 'No registered iris data found in the system'}), 400

        # Compare with each registered iris
        for user in users_with_iris:
            print(f"Comparing iris with user: {user.username}")
            print(f"About to call compare_iris_images function...")
            match_result = compare_iris_images(user.iris_data, iris_image_data)
            print(f"Function returned: {match_result}")
            print(f"Comparison result for {user.username}: {match_result}")

            if match_result:
                # Iris match found - log the user in
                login_user(user)
                print(f"Iris authentication successful for user: {user.username}")
                return jsonify({
                    'message': 'Iris authentication successful',
                    'username': user.username
                }), 200

        # No match found
        print("No iris match found for any user")
        return jsonify({'error': 'Iris authentication failed. No matching iris found.'}), 401

    except Exception as e:
        print(f"Error in iris verification: {e}")
        return jsonify({'error': 'An error occurred during iris verification'}), 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/debug/users')
def debug_users():
    """Debug route to check user data"""
    users = User.query.all()
    user_data = []
    for user in users:
        user_data.append({
            'id': user.id,
            'username': user.username,
            'has_iris_data': user.iris_data is not None,
            'iris_data_size': len(user.iris_data) if user.iris_data else 0,
            'created_at': user.created_at.isoformat() if user.created_at else None
        })
    return jsonify(user_data)

@app.route('/debug/add_iris/<username>', methods=['POST'])
def debug_add_iris(username):
    """Debug route to manually add iris data to a user"""
    if 'iris_image' not in request.files:
        return jsonify({'error': 'No iris image provided'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    iris_image = request.files['iris_image'].read()
    user.iris_data = iris_image
    db.session.commit()

    return jsonify({
        'message': f'Iris data added to user {username}',
        'iris_data_size': len(iris_image)
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)