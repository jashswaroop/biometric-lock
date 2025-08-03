document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('videoElement');
    const canvas = document.getElementById('canvasElement');
    const startScanBtn = document.getElementById('startScan');
    const captureIrisBtn = document.getElementById('captureIris');
    const enrollIrisBtn = document.getElementById('enrollIris');
    const enrollmentStatus = document.getElementById('enrollmentStatus');
    const scanStatus = document.getElementById('scanStatus');
    const matchStatus = document.getElementById('matchStatus');
    let stream = null;

    // Initialize camera access
    async function initializeCamera() {
        console.log('Initializing camera...');
        if (!video) {
            console.log('No video element found on page');
            return; // Skip if no video element on page
        }

        try {
            console.log('Requesting camera access...');
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: 640,
                    height: 480,
                    facingMode: 'user'
                }
            });
            video.srcObject = stream;
            console.log('Camera access granted');
            updateStatus('Camera initialized successfully', 'success');

            // Enable buttons once camera is ready
            if (startScanBtn) {
                startScanBtn.disabled = false;
                console.log('Start scan button enabled');
            }
            if (captureIrisBtn) {
                captureIrisBtn.disabled = false;
                console.log('Capture iris button enabled');
            }
            if (enrollIrisBtn) {
                enrollIrisBtn.disabled = false;
                console.log('Enroll iris button enabled');
            }

            // Hide enrollment status and show success
            if (enrollmentStatus) {
                enrollmentStatus.className = 'alert alert-success';
                enrollmentStatus.innerHTML = '<span>Camera ready! You can now capture your iris.</span>';
                enrollmentStatus.classList.remove('d-none');
            }
        } catch (err) {
            console.error('Camera access error:', err);
            updateStatus('Failed to access camera: ' + err.message, 'danger');

            if (enrollmentStatus) {
                enrollmentStatus.className = 'alert alert-danger';
                enrollmentStatus.innerHTML = '<span>Camera access failed. Please allow camera permissions and refresh the page.</span>';
                enrollmentStatus.classList.remove('d-none');
            }
        }
    }

    // Update status messages
    function updateStatus(message, type = 'info') {
        if (scanStatus) {
            scanStatus.className = `alert alert-${type}`;
            scanStatus.textContent = message;
        }
        if (enrollmentStatus && !scanStatus) {
            enrollmentStatus.className = `alert alert-${type}`;
            enrollmentStatus.innerHTML = `<span>${message}</span>`;
            enrollmentStatus.classList.remove('d-none');
        }
    }

    // Capture iris image from video
    function captureIris() {
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        return new Promise((resolve) => {
            canvas.toBlob((blob) => {
                resolve(blob);
            }, 'image/jpeg', 0.95);
        });
    }

    // Handle iris enrollment during registration
    async function handleIrisEnrollment() {
        try {
            updateStatus('Capturing iris image...', 'info');
            const irisBlob = await captureIris();

            const formData = new FormData();
            formData.append('iris_image', irisBlob);

            const response = await fetch('/capture_iris_registration', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                updateStatus('Iris captured successfully! You can now complete registration.', 'success');

                // Enable the registration button
                const registerButton = document.getElementById('registerButton');
                if (registerButton) {
                    registerButton.disabled = false;
                    registerButton.textContent = 'Complete Registration';
                }

                // Disable the capture button since iris is already captured
                if (captureIrisBtn) {
                    captureIrisBtn.disabled = true;
                    captureIrisBtn.textContent = 'Iris Captured ✓';
                    captureIrisBtn.classList.remove('btn-primary');
                    captureIrisBtn.classList.add('btn-success');
                }
            } else {
                throw new Error(result.error || 'Failed to enroll iris');
            }
        } catch (err) {
            updateStatus('Enrollment failed: ' + err.message, 'danger');
            console.error('Enrollment error:', err);
        }
    }

    // Handle iris enrollment for logged-in users
    async function handleIrisEnrollmentForLoggedInUser() {
        try {
            updateStatus('Capturing iris image...', 'info');
            const irisBlob = await captureIris();

            const formData = new FormData();
            formData.append('iris_image', irisBlob);

            const response = await fetch('/capture_iris', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                updateStatus('Iris enrolled successfully! You can now use iris authentication.', 'success');

                // Disable the enroll button since iris is already captured
                if (enrollIrisBtn) {
                    enrollIrisBtn.disabled = true;
                    enrollIrisBtn.textContent = 'Iris Enrolled ✓';
                    enrollIrisBtn.classList.remove('btn-success');
                    enrollIrisBtn.classList.add('btn-secondary');
                }
            } else {
                throw new Error(result.error || 'Failed to enroll iris');
            }
        } catch (err) {
            updateStatus('Enrollment failed: ' + err.message, 'danger');
            console.error('Enrollment error:', err);
        }
    }

    // Handle iris verification
    async function handleIrisVerification() {
        try {
            updateStatus('Scanning iris...', 'info');
            const irisBlob = await captureIris();
            
            const formData = new FormData();
            formData.append('iris_image', irisBlob);

            const response = await fetch('/verify_iris', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (response.ok) {
                updateStatus('Authentication successful!', 'success');
                setTimeout(() => window.location.href = '/', 1500);
            } else {
                throw new Error(result.error || 'Authentication failed');
            }
        } catch (err) {
            updateStatus('Verification failed: ' + err.message, 'danger');
            console.error('Verification error:', err);
        }
    }

    // Handle form submissions
    const registerForm = document.getElementById('registrationForm');
    if (registerForm) {
        // Enable registration button when form fields are filled
        const usernameField = document.getElementById('username');
        const passwordField = document.getElementById('password');
        const confirmPasswordField = document.getElementById('confirmPassword');
        const registerButton = document.getElementById('registerButton');

        function checkFormValidity() {
            const username = usernameField.value.trim();
            const password = passwordField.value;
            const confirmPassword = confirmPasswordField.value;

            if (username && password && confirmPassword && password === confirmPassword) {
                if (registerButton) registerButton.disabled = false;
            } else {
                if (registerButton) registerButton.disabled = true;
            }
        }

        // Add event listeners to form fields
        if (usernameField) usernameField.addEventListener('input', checkFormValidity);
        if (passwordField) passwordField.addEventListener('input', checkFormValidity);
        if (confirmPasswordField) confirmPasswordField.addEventListener('input', checkFormValidity);

        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;

            if (password !== confirmPassword) {
                updateStatus('Passwords do not match', 'danger');
                return;
            }

            try {
                updateStatus('Creating account...', 'info');
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, password })
                });

                const result = await response.json();

                if (response.ok) {
                    updateStatus('Registration successful! Redirecting to login...', 'success');
                    setTimeout(() => window.location.href = '/login', 1500);
                } else {
                    throw new Error(result.error || 'Registration failed');
                }
            } catch (err) {
                updateStatus('Registration failed: ' + err.message, 'danger');
            }
        });
    }

    // Handle login form
    const loginForm = document.getElementById('passwordLoginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;

            console.log('Login attempt:', { username, password: '***' });

            try {
                const requestBody = JSON.stringify({ username, password });
                console.log('Request body:', requestBody);

                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: requestBody
                });

                console.log('Response status:', response.status);
                console.log('Response headers:', response.headers);

                const result = await response.json();
                console.log('Response data:', result);

                if (response.ok) {
                    updateStatus('Login successful! Redirecting...', 'success');
                    setTimeout(() => window.location.href = '/', 1000);
                } else {
                    throw new Error(result.error || 'Login failed');
                }
            } catch (err) {
                console.error('Login error:', err);
                updateStatus('Login failed: ' + err.message, 'danger');
            }
        });
    }

    // Event listeners
    if (startScanBtn) {
        console.log('Adding event listener to start scan button');
        startScanBtn.addEventListener('click', handleIrisVerification);
    }

    if (captureIrisBtn) {
        console.log('Adding event listener to capture iris button');
        captureIrisBtn.addEventListener('click', handleIrisEnrollment);
    } else {
        console.log('Capture iris button not found');
    }

    if (enrollIrisBtn) {
        console.log('Adding event listener to enroll iris button');
        enrollIrisBtn.addEventListener('click', handleIrisEnrollmentForLoggedInUser);
    } else {
        console.log('Enroll iris button not found');
    }

    // Initialize camera when page loads
    initializeCamera();

    // Cleanup
    window.addEventListener('beforeunload', () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
});