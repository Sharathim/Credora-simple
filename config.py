import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Storage directories
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
UPLOAD_DIR = os.path.join(STORAGE_DIR, "uploads")
PROCESSED_DIR = os.path.join(STORAGE_DIR, "processed")
SAMPLES_DIR = os.path.join(BASE_DIR, "static", "sample_certs")
DB_PATH = os.path.join(STORAGE_DIR, "certificates.db")

# Ensure required directories exist
for directory in [STORAGE_DIR, UPLOAD_DIR, PROCESSED_DIR, SAMPLES_DIR]:
    os.makedirs(directory, exist_ok=True)

# Quality Checker Thresholds
QUALITY_THRESHOLDS = {
    "MIN_WIDTH": 500,
    "MIN_HEIGHT": 350,
    "MIN_SHARPNESS": 80.0,       # Laplacian variance
    "MIN_BRIGHTNESS": 35.0,      # Mean pixel luminance (0-255)
    "MAX_BRIGHTNESS": 248.0,     # Max pixel luminance (0-255)
    "MIN_CONTRAST": 25.0,        # RMS contrast (std dev of luminance)
    "MIN_DOC_AREA_RATIO": 0.18,  # Minimum document area relative to frame
    "MAX_PERSPECTIVE_SKEW": 45.0 # Max skew angle before rejection (degrees)
}

# Perceptual Hashing & Matching
MATCH_THRESHOLD = 85.0          # Default visual similarity percentage for a MATCH
PHASH_SIZE = 8                  # 8x8 = 64-bit pHash
CANONICAL_SIZE = (1000, 700)    # Standardized (width, height) for normalized comparison
