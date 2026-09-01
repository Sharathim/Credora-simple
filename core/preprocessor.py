"""
Image Preprocessor Module
=========================
Performs document boundary cropping, 4-point perspective warp transform,
rotation alignment, illumination normalization (CLAHE), and canonical resizing.
Ensures photographs/scans are transformed into standardized canonical representation.
"""

import cv2
import numpy as np
from config import CANONICAL_SIZE


class ImagePreprocessor:
    def __init__(self, target_size=CANONICAL_SIZE):
        self.target_width, self.target_height = target_size

    def preprocess(self, image_np, corners=None):
        """
        Executes full preprocessing pipeline:
        1. Document edge detection & 4-point perspective transform
        2. Aspect ratio / rotation alignment
        3. Canonical resizing (1000x700)
        4. Lighting / contrast normalization via CLAHE
        5. Grayscale conversion for perceptual fingerprinting

        Returns:
            dict: {
                'gray_canonical': np.ndarray (1000x700 single channel),
                'color_canonical': np.ndarray (1000x700 3-channel BGR for UI display),
                'perspective_corrected': bool,
                'rotation_applied': int (0, 90, 180, 270)
            }
        """
        if image_np is None or image_np.size == 0:
            raise ValueError("Input image is invalid or empty.")

        img = image_np.copy()
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        perspective_corrected = False
        rotation_deg = 0

        # Step 1: Detect corners if not provided
        if corners is None:
            corners = self._find_document_corners(img)

        # Step 2: 4-Point Perspective Transform
        if corners is not None and len(corners) == 4:
            warped = self._four_point_transform(img, corners)
            perspective_corrected = True
        else:
            warped = img

        # Step 3: Rotation & Orientation alignment (Ensure Landscape format for certificates)
        h, w = warped.shape[:2]
        if h > w * 1.15:  # Portrait document, rotate 90 degrees clockwise to standardize landscape
            warped = cv2.rotate(warped, cv2.ROTATE_90_CLOCKWISE)
            rotation_deg = 90
            h, w = warped.shape[:2]

        # Step 4: Standard Canonical Resizing (e.g. 1000 x 700)
        color_canonical = cv2.resize(warped, (self.target_width, self.target_height), interpolation=cv2.INTER_AREA)

        # Step 5: Convert to Grayscale & Normalize (Contrast Stretch + Soft Smoothing)
        gray = cv2.cvtColor(color_canonical, cv2.COLOR_BGR2GRAY)
        gray_smoothed = cv2.GaussianBlur(gray, (3, 3), 0)
        gray_normalized = cv2.normalize(gray_smoothed, None, 0, 255, cv2.NORM_MINMAX)

        return {
            "gray_canonical": gray_normalized,
            "color_canonical": color_canonical,
            "perspective_corrected": perspective_corrected,
            "rotation_applied": rotation_deg
        }

    def _find_document_corners(self, img):
        """Finds 4-point document corners from image using Canny and polygon approximation."""
        h, w = img.shape[:2]
        total_area = float(w * h)
        scale = 600.0 / max(w, h)
        small = cv2.resize(img, (int(w * scale), int(h * scale)))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 200)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            area = cv2.contourArea(c) / (scale * scale)
            if len(approx) == 4 and (area / total_area) > 0.20:
                return approx.reshape(4, 2) / scale

        return None

    def _four_point_transform(self, image, pts):
        """Applies 4-point OpenCV perspective warp transform."""
        rect = self._order_points(pts)
        (tl, tr, br, bl) = rect

        # Compute width of new image
        width_a = np.linalg.norm(br - bl)
        width_b = np.linalg.norm(tr - tl)
        max_width = max(int(width_a), int(width_b))

        # Compute height of new image
        height_a = np.linalg.norm(tr - br)
        height_b = np.linalg.norm(tl - bl)
        max_height = max(int(height_a), int(height_b))

        dst = np.array([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]
        ], dtype="float32")

        # Compute perspective transform matrix and warp
        matrix = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, matrix, (max_width, max_height), flags=cv2.INTER_CUBIC)
        return warped

    def _order_points(self, pts):
        """Orders points: top-left, top-right, bottom-right, bottom-left."""
        pts = np.array(pts, dtype="float32")
        rect = np.zeros((4, 2), dtype="float32")

        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect
