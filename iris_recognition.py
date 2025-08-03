import cv2
import numpy as np
import dlib
from PIL import Image
import io
from typing import Tuple, Optional

class IrisRecognition:
    def __init__(self):
        # Initialize dlib's face detector and facial landmarks predictor
        self.detector = dlib.get_frontal_face_detector()
        # You'll need to download the shape predictor file and update this path
        self.predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

    def _extract_eye_region(self, image: np.ndarray, landmarks) -> Tuple[np.ndarray, np.ndarray]:
        """Extract left and right eye regions from the image using facial landmarks."""
        # Define eye landmark indices
        left_eye = [(landmarks.part(36+i).x, landmarks.part(36+i).y) for i in range(6)]
        right_eye = [(landmarks.part(42+i).x, landmarks.part(42+i).y) for i in range(6)]

        # Convert to numpy arrays
        left_eye = np.array(left_eye, dtype=np.int32)
        right_eye = np.array(right_eye, dtype=np.int32)

        # Create masks for both eyes
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [left_eye], 255)
        cv2.fillPoly(mask, [right_eye], 255)

        # Extract eye regions
        eye_region = cv2.bitwise_and(image, image, mask=mask)

        # Get bounding rectangles for both eyes
        left_x, left_y, left_w, left_h = cv2.boundingRect(left_eye)
        right_x, right_y, right_w, right_h = cv2.boundingRect(right_eye)

        # Extract individual eye regions
        left_eye_region = image[left_y:left_y+left_h, left_x:left_x+left_w]
        right_eye_region = image[right_y:right_y+right_h, right_x:right_x+right_w]

        return left_eye_region, right_eye_region

    def _process_eye_region(self, eye_region: np.ndarray) -> Optional[np.ndarray]:
        """Process the eye region to isolate and enhance the iris."""
        if eye_region.size == 0:
            return None

        # Convert to grayscale
        gray_eye = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY)

        # Apply histogram equalization
        gray_eye = cv2.equalizeHist(gray_eye)

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray_eye, (7, 7), 0)

        # Detect iris using Hough Circle Transform
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=20,
            param1=50,
            param2=30,
            minRadius=10,
            maxRadius=30
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            x, y, r = circles[0][0]

            # Create a mask for the iris
            mask = np.zeros_like(gray_eye)
            cv2.circle(mask, (x, y), r, 255, -1)

            # Extract iris region
            iris = cv2.bitwise_and(gray_eye, gray_eye, mask=mask)

            # Normalize iris region to fixed size
            iris = cv2.resize(iris, (100, 100))

            return iris

        return None

    def _extract_iris_features(self, iris: np.ndarray) -> Optional[np.ndarray]:
        """Extract features from the iris region using Gabor filters."""
        if iris is None:
            return None

        # Apply multiple Gabor filters
        features = []
        for theta in np.arange(0, np.pi, np.pi/4):
            for freq in [0.1, 0.2, 0.3]:
                kernel = cv2.getGaborKernel(
                    ksize=(21, 21),
                    sigma=5,
                    theta=theta,
                    lambd=1/freq,
                    gamma=0.5,
                    psi=0
                )
                filtered = cv2.filter2D(iris, cv2.CV_8UC3, kernel)
                features.append(filtered.flatten())

        return np.concatenate(features)

    def process_image(self, image_data: bytes) -> Optional[np.ndarray]:
        """Process the image data and extract iris features."""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Detect faces
            faces = self.detector(image)
            if not faces:
                return None

            # Get facial landmarks
            landmarks = self.predictor(image, faces[0])

            # Extract eye regions
            left_eye, right_eye = self._extract_eye_region(image, landmarks)

            # Process both eyes
            left_iris = self._process_eye_region(left_eye)
            right_iris = self._process_eye_region(right_eye)

            # Extract features from both irises
            left_features = self._extract_iris_features(left_iris)
            right_features = self._extract_iris_features(right_iris)

            if left_features is not None and right_features is not None:
                return np.concatenate([left_features, right_features])

        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return None

        return None

    def compare_iris_features(self, features1: np.ndarray, features2: np.ndarray, threshold: float = 0.8) -> bool:
        """Compare two sets of iris features and determine if they match."""
        if features1 is None or features2 is None:
            return False

        # Normalize features
        features1_norm = features1 / np.linalg.norm(features1)
        features2_norm = features2 / np.linalg.norm(features2)

        # Calculate cosine similarity
        similarity = np.dot(features1_norm, features2_norm)

        return similarity >= threshold