# Biometric Lock System with Iris Recognition

A secure biometric authentication system that uses iris recognition for user verification. This system provides a web-based interface for user registration, iris enrollment, and authentication.

## Features

- Real-time iris scanning and recognition
- Dual authentication methods (password and iris)
- Secure user account management
- Modern, responsive web interface
- Real-time feedback and status updates
- Access history tracking
- Secure data storage with encryption

## Prerequisites

- Python 3.8 or higher
- Webcam or camera device
- Modern web browser with WebRTC support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/biometric-lock.git
cd biometric-lock
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Unix or MacOS:
```bash
source venv/bin/activate
```

4. Install required packages:
```bash
pip install -r requirements.txt
```

5. Download the shape predictor file:
- Download `shape_predictor_68_face_landmarks.dat` from the dlib website
- Place it in the root directory of the project

## Configuration

1. Create a `.env` file in the project root:
```env
FLASK_SECRET_KEY=your_secret_key_here
DEBUG=True
DATABASE_URL=sqlite:///biometric.db
```

2. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Access the application:
- Open your web browser
- Navigate to `http://localhost:5000`

## Usage

### Registration
1. Click "Register" on the homepage
2. Fill in your username and password
3. Follow the iris enrollment process
4. Complete registration

### Authentication
1. Choose either password or iris authentication
2. For iris authentication:
   - Position your face in front of the camera
   - Follow the on-screen instructions
   - Stay still during the scanning process
3. Wait for verification

## Security Features

- Encrypted storage of biometric data
- Rate limiting for authentication attempts
- Secure session management
- HTTPS support
- Protection against common web vulnerabilities

## System Architecture

### Frontend
- HTML5, CSS3, JavaScript
- Bootstrap 5 for responsive design
- WebRTC for camera access
- Real-time feedback system

### Backend
- Flask web framework
- SQLAlchemy ORM
- OpenCV for image processing
- dlib for facial landmark detection
- Custom iris recognition algorithm

### Database
- SQLite for development
- Support for PostgreSQL in production

## API Endpoints

- `/register` - User registration
- `/login` - User authentication
- `/capture_iris` - Iris enrollment
- `/verify_iris` - Iris verification
- `/logout` - User logout

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenCV community
- dlib developers
- Flask framework team
- Bootstrap team

## Support

For support, please open an issue in the GitHub repository or contact the development team.

## Disclaimer

This system is for educational and demonstration purposes. For production use, additional security measures and thorough testing are recommended.