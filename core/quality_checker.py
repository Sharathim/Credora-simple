"""
Image Quality Checker Module
=============================
Evaluates the suitability of uploaded certificate images before preprocessing
and perceptual hashing. Inspects blur (Laplacian variance), brightness, contrast,
resolution, document visibility, perspective angle, and obstruction.
"""

import cv2
import numpy as np
from config import QUALITY_THRESHOLDS


class QualityChecker:
    def __init__(self, thresholds=None):
        self.cfg = thresholds or QUALITY_THRESHOLDS

    def inspect(self, image_np):
        """
        Runs comprehensive image quality checks on an input BGR or Grayscale image.
        Returns:
            dict: {
                'passed': bool,
                'summary': str,
                'checks': dict of individual check details,
                'detected_corners': list of 4 points (if found) or None,
                'metrics': dict of raw numerical values
            }
        """
        if image_np is None or image_np.size == 0:
            return {
                "passed": False,
                "summary": "❌ Invalid or corrupted image file.",
                "checks": {},
                "detected_corners": None,
                "metrics": {}
            }

        # Convert to Grayscale
        if len(image_np.shape) == 3:
            gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
            height, width, _ = image_np.shape
        else:
            gray = image_np.copy()
            height, width = image_np.shape

        checks = {}
        passed_all = True
        failure_reasons = []

        # 1. Resolution Check
        res_ok = (width >= self.cfg["MIN_WIDTH"]) and (height >= self.cfg["MIN_HEIGHT"])
        checks["resolution"] = {
            "name": "Resolution",
            "status": "pass" if res_ok else "fail",
            "value": f"{width} × {height} px",
            "message": "✅ Good" if res_ok else f"❌ Resolution too low (minimum {self.cfg['MIN_WIDTH']}x{self.cfg['MIN_HEIGHT']} px required)."
        }
        if not res_ok:
            passed_all = False
            failure_reasons.append(checks["resolution"]["message"])

        # 2. Sharpness / Blur Check (Laplacian Variance)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        sharpness_ok = laplacian_var >= self.cfg["MIN_SHARPNESS"]
        checks["sharpness"] = {
            "name": "Sharpness",
            "status": "pass" if sharpness_ok else "fail",
            "value": f"{laplacian_var:.1f} (Threshold: {self.cfg['MIN_SHARPNESS']})",
            "message": "✅ Good" if sharpness_ok else "❌ Image is too blurry. Please take another photograph or provide a sharper scan."
        }
        if not sharpness_ok:
            passed_all = False
            failure_reasons.append(checks["sharpness"]["message"])

        # 3. Brightness Check (Mean pixel luminance)
        mean_brightness = float(np.mean(gray))
        if mean_brightness < self.cfg["MIN_BRIGHTNESS"]:
            bright_status = "fail"
            bright_msg = "❌ Image is too dark. Please retake the photograph with better lighting."
            passed_all = False
            failure_reasons.append(bright_msg)
        elif mean_brightness > self.cfg["MAX_BRIGHTNESS"]:
            bright_status = "fail"
            bright_msg = "❌ Image is overexposed/too bright with glare. Please adjust lighting."
            passed_all = False
            failure_reasons.append(bright_msg)
        else:
            bright_status = "pass"
            bright_msg = "✅ Good"

        checks["brightness"] = {
            "name": "Brightness",
            "status": bright_status,
            "value": f"{mean_brightness:.1f} / 255",
            "message": bright_msg
        }

        # 4. Contrast Check (Standard Deviation of luminance)
        std_contrast = float(np.std(gray))
        contrast_ok = std_contrast >= self.cfg["MIN_CONTRAST"]
        checks["contrast"] = {
            "name": "Contrast",
            "status": "pass" if contrast_ok else "fail",
            "value": f"{std_contrast:.1f} (Min: {self.cfg['MIN_CONTRAST']})",
            "message": "✅ Good" if contrast_ok else "❌ Insufficient contrast for reliable document verification."
        }
        if not contrast_ok:
            passed_all = False
            failure_reasons.append(checks["contrast"]["message"])

        # 5. Document Visibility & Contour Analysis
        corners, doc_area_ratio, skew_angle = self._detect_document_geometry(gray, width, height)

        vis_ok = doc_area_ratio >= self.cfg["MIN_DOC_AREA_RATIO"]
        checks["document_visibility"] = {
            "name": "Document Visibility",
            "status": "pass" if vis_ok else "fail",
            "value": f"{doc_area_ratio * 100:.1f}% frame area",
            "message": "✅ Good" if vis_ok else "❌ Certificate occupies too small a portion of the image or is heavily cropped."
        }
        if not vis_ok:
            passed_all = False
            failure_reasons.append(checks["document_visibility"]["message"])

        # 6. Perspective / Angle Check
        angle_ok = skew_angle <= self.cfg["MAX_PERSPECTIVE_SKEW"]
        angle_msg = "✅ Good"
        if not angle_ok:
            angle_msg = f"❌ Certificate angle is too extreme ({skew_angle:.1f}°). Please take a photograph directly above the document."
            passed_all = False
            failure_reasons.append(angle_msg)
        elif skew_angle > 8.0:
            angle_msg = f"✅ Skew detected ({skew_angle:.1f}°), will auto-correct perspective."

        checks["document_angle"] = {
            "name": "Document Angle",
            "status": "pass" if angle_ok else "fail",
            "value": f"{skew_angle:.1f}° skew",
            "message": angle_msg
        }

        # 7. Obstruction / Shadow Check
        obstruction_detected, obs_msg = self._check_obstruction(gray, corners)
        checks["obstruction"] = {
            "name": "Obstruction & Occlusion",
            "status": "fail" if obstruction_detected else "pass",
            "value": "Clean" if not obstruction_detected else "Potential obstruction",
            "message": "✅ Good" if not obstruction_detected else obs_msg
        }
        if obstruction_detected:
            passed_all = False
            failure_reasons.append(obs_msg)

        summary = "Image accepted — ready for verification." if passed_all else " ".join(failure_reasons)

        return {
            "passed": passed_all,
            "summary": summary,
            "checks": checks,
            "detected_corners": corners,
            "metrics": {
                "width": width,
                "height": height,
                "laplacian_var": round(laplacian_var, 2),
                "mean_brightness": round(mean_brightness, 2),
                "contrast": round(std_contrast, 2),
                "doc_area_ratio": round(doc_area_ratio, 3),
                "skew_angle": round(skew_angle, 2)
            }
        }

    def _detect_document_geometry(self, gray, width, height):
        """
        Attempts to detect document boundary polygon and calculate skew angle.
        """
        total_area = float(width * height)
        # Downscale for fast robust contour searching
        scale = 600.0 / max(width, height)
        small_w = int(width * scale)
        small_h = int(height * scale)
        small_gray = cv2.resize(gray, (small_w, small_h))

        # Edge detection
        blurred = cv2.GaussianBlur(small_gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 200)

        # Dilate to connect broken contours
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        detected_corners = None
        doc_area_ratio = 1.0  # Default assumption: image is a direct scan filling frame
        skew_angle = 0.0

        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            area = cv2.contourArea(c) / (scale * scale)
            ratio = area / total_area

            # If a significant 4-corner polygon is found
            if len(approx) == 4 and ratio > 0.15:
                # Scale corners back to original image size
                orig_corners = approx.reshape(4, 2) / scale
                detected_corners = orig_corners.tolist()
                doc_area_ratio = ratio

                # Calculate skew from the 4 corners
                skew_angle = self._calculate_skew_angle(orig_corners)
                break

        # If no distinct quad contour found, check if overall image is the document
        if detected_corners is None:
            doc_area_ratio = 1.0  # Document fills the whole photo/scan
            skew_angle = 0.0

        return detected_corners, doc_area_ratio, skew_angle

    def _calculate_skew_angle(self, corners):
        """
        Calculates the maximum perspective skew angle and keystone distortion among the edges.
        """
        try:
            rect = self._order_points(corners)
            (tl, tr, br, bl) = rect

            # Compute horizontal edge angles
            top_dx, top_dy = tr[0] - tl[0], tr[1] - tl[1]
            bot_dx, bot_dy = br[0] - bl[0], br[1] - bl[1]

            angle_top = abs(np.degrees(np.arctan2(top_dy, top_dx)))
            angle_bot = abs(np.degrees(np.arctan2(bot_dy, bot_dx)))

            # Compute vertical edge deviation from 90 deg
            left_dx, left_dy = bl[0] - tl[0], bl[1] - tl[1]
            right_dx, right_dy = br[0] - tr[0], br[1] - tr[1]

            angle_left = abs(90.0 - abs(np.degrees(np.arctan2(left_dy, left_dx))))
            angle_right = abs(90.0 - abs(np.degrees(np.arctan2(right_dy, right_dx))))

            max_edge_skew = max(angle_top, angle_bot, angle_left, angle_right)

            # Keystone / perspective ratio check
            top_w = np.linalg.norm(tr - tl)
            bot_w = np.linalg.norm(br - bl)
            left_h = np.linalg.norm(bl - tl)
            right_h = np.linalg.norm(br - tr)

            w_ratio = abs(top_w - bot_w) / max(top_w, bot_w, 1.0)
            h_ratio = abs(left_h - right_h) / max(left_h, right_h, 1.0)
            keystone_skew = max(w_ratio, h_ratio) * 60.0  # Scale keystone ratio to equivalent degrees

            total_skew = max(max_edge_skew, keystone_skew)
            return float(total_skew)
        except Exception:
            return 0.0

    def _order_points(self, pts):
        """
        Orders coordinates: top-left, top-right, bottom-right, bottom-left
        """
        pts = np.array(pts, dtype="float32")
        rect = np.zeros((4, 2), dtype="float32")

        # Top-left has smallest sum, bottom-right has largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # Top-right has smallest diff (y - x), bottom-left has largest diff
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect

    def _check_obstruction(self, gray, corners):
        """
        Checks if a large portion of the central region is occluded by dark objects or fingers.
        """
        h, w = gray.shape
        # Center region 30% to 70%
        center_crop = gray[int(h * 0.3):int(h * 0.7), int(w * 0.3):int(w * 0.7)]
        if center_crop.size == 0:
            return False, "✅ Good"

        # Check for unusually high percentage of pitch black pixels (obstruction/shadow)
        black_pixels = np.sum(center_crop < 15)
        black_ratio = black_pixels / float(center_crop.size)

        if black_ratio > 0.30:
            return True, "❌ Significant obstruction or heavy shadow detected over certificate content."

        return False, "✅ Good"
