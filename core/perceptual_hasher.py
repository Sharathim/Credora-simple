"""
Perceptual Image Hasher Module
==============================
Perceptual hashing (pHash, dHash, aHash, wHash) creates a compact, invariant visual
fingerprint of an image. Unlike cryptographic hash functions (e.g., SHA-256 or MD5)
where a single modified bit changes the entire hash completely (the avalanche effect),
perceptual hash fingerprints change proportionally to visual changes.

Visual modifications such as:
  - Downscaling / Resizing
  - Moderate JPEG compression & artifacts
  - Uniform brightness or contrast shifts
  - Conversion to grayscale
  - Minor perspective transformation or camera photo capture
will still yield very close perceptual fingerprints with a low Hamming distance.
"""

from PIL import Image
import imagehash
import numpy as np


class PerceptualHasher:
    """
    Computes perceptual fingerprints and calculates visual similarity scores
    using Hamming distance.
    """

    def __init__(self, hash_size=8):
        # hash_size=8 produces an 8x8 = 64-bit fingerprint
        self.hash_size = hash_size
        self.total_bits = hash_size * hash_size

    def compute_all_hashes(self, image_np):
        """
        Computes pHash (primary), dHash, aHash, and wHash for a preprocessed image.
        Accepts NumPy grayscale array or BGR array.

        Returns:
            dict: Hexadecimal representations of the hashes.
        """
        if isinstance(image_np, np.ndarray):
            pil_img = Image.fromarray(image_np)
        else:
            pil_img = image_np

        phash = imagehash.phash(pil_img, hash_size=self.hash_size)
        dhash = imagehash.dhash(pil_img, hash_size=self.hash_size)
        ahash = imagehash.average_hash(pil_img, hash_size=self.hash_size)
        try:
            whash = imagehash.whash(pil_img, hash_size=self.hash_size)
        except Exception:
            whash = phash  # Fallback if pywt is unavailable

        return {
            "phash": str(phash),
            "dhash": str(dhash),
            "ahash": str(ahash),
            "whash": str(whash),
            "bit_length": self.total_bits
        }

    def compare(self, hash_hex_1, hash_hex_2, bit_length=None):
        """
        Calculates Hamming distance and similarity percentage between two perceptual hashes.

        Formula:
            Hamming Distance = count of differing bits between hash_1 and hash_2
            Similarity Percentage = (1.0 - (Hamming Distance / Total Bits)) * 100%

        Returns:
            dict: {
                'hamming_distance': int,
                'max_distance': int,
                'similarity_percentage': float (0.0 to 100.0)
            }
        """
        bits = bit_length or self.total_bits
        h1 = imagehash.hex_to_hash(hash_hex_1)
        h2 = imagehash.hex_to_hash(hash_hex_2)

        hamming_dist = int(h1 - h2)
        similarity = max(0.0, min(100.0, (1.0 - (hamming_dist / float(bits))) * 100.0))

        return {
            "hamming_distance": hamming_dist,
            "max_distance": bits,
            "similarity_percentage": round(similarity, 2)
        }

    def evaluate_verification(self, issuer_hashes, verifier_hashes, threshold=85.0):
        """
        Compares all hash variants (pHash, dHash, aHash, wHash) and evaluates the final decision
        against the configurable threshold.

        Returns:
            dict: Detailed comparison report including individual scores and final decision.
        """
        phash_res = self.compare(issuer_hashes["phash"], verifier_hashes["phash"])
        dhash_res = self.compare(issuer_hashes["dhash"], verifier_hashes["dhash"])
        ahash_res = self.compare(issuer_hashes["ahash"], verifier_hashes["ahash"])

        whash_res = None
        if "whash" in issuer_hashes and "whash" in verifier_hashes:
            whash_res = self.compare(issuer_hashes["whash"], verifier_hashes["whash"])

        primary_sim = phash_res["similarity_percentage"]
        is_match = primary_sim >= threshold

        status_text = (
            "Certificate appears visually consistent with the issuer's original."
            if is_match
            else "The uploaded certificate differs significantly from the issuer's original."
        )

        return {
            "decision": "MATCH" if is_match else "MISMATCH",
            "is_match": is_match,
            "primary_similarity": primary_sim,
            "hamming_distance": phash_res["hamming_distance"],
            "threshold_used": threshold,
            "status_text": status_text,
            "hash_breakdown": {
                "phash": {
                    "name": "pHash (DCT - Primary)",
                    "similarity": primary_sim,
                    "hamming_dist": phash_res["hamming_distance"]
                },
                "dhash": {
                    "name": "dHash (Gradient)",
                    "similarity": dhash_res["similarity_percentage"],
                    "hamming_dist": dhash_res["hamming_distance"]
                },
                "ahash": {
                    "name": "aHash (Average Luminance)",
                    "similarity": ahash_res["similarity_percentage"],
                    "hamming_dist": ahash_res["hamming_distance"]
                },
                "whash": {
                    "name": "wHash (Wavelet)",
                    "similarity": whash_res["similarity_percentage"] if whash_res else primary_sim,
                    "hamming_dist": whash_res["hamming_distance"] if whash_res else phash_res["hamming_distance"]
                }
            }
        }


class RegionHasher:
    """
    Modular Region-Based Comparison Architecture.
    Allows independent perceptual hashing of discrete document regions
    (Student Photo, University Seal, Signature Line, Crest / Header, Body Text).
    """

    # Canonical normalized relative coordinates [ymin, xmin, ymax, xmax] (0.0 to 1.0)
    DEFAULT_REGIONS = {
        "header_crest": (0.04, 0.25, 0.22, 0.75),   # Top center logo/crest
        "student_photo": (0.24, 0.78, 0.52, 0.94),  # Right side student photo
        "body_text": (0.28, 0.10, 0.68, 0.75),      # Central conferral text
        "official_seal": (0.70, 0.10, 0.95, 0.32),  # Bottom left seal
        "signature": (0.72, 0.65, 0.95, 0.92)       # Bottom right signature
    }

    def __init__(self, hasher=None):
        self.hasher = hasher or PerceptualHasher(hash_size=8)

    def extract_regions(self, image_canonical_np):
        """
        Extracts cropped NumPy images for each defined region from a canonical (1000x700) document.
        """
        h, w = image_canonical_np.shape[:2]
        region_crops = {}

        for name, (ymin_r, xmin_r, ymax_r, xmax_r) in self.DEFAULT_REGIONS.items():
            y1 = int(ymin_r * h)
            y2 = int(ymax_r * h)
            x1 = int(xmin_r * w)
            x2 = int(xmax_r * w)
            crop = image_canonical_np[y1:y2, x1:x2]
            region_crops[name] = crop

        return region_crops

    def compute_region_hashes(self, image_canonical_np):
        """
        Computes independent perceptual hashes for each document region.
        """
        crops = self.extract_regions(image_canonical_np)
        region_hashes = {}
        for name, crop in crops.items():
            if crop.size > 0:
                region_hashes[name] = self.hasher.compute_all_hashes(crop)["phash"]
            else:
                region_hashes[name] = None
        return region_hashes

    def compare_regions(self, issuer_region_hashes, verifier_region_hashes, threshold=85.0):
        """
        Compares each region independently to pinpoint specific localized alterations.
        """
        results = {}
        for name in self.DEFAULT_REGIONS.keys():
            h1 = issuer_region_hashes.get(name)
            h2 = verifier_region_hashes.get(name)
            if h1 and h2:
                res = self.hasher.compare(h1, h2)
                results[name] = {
                    "similarity": res["similarity_percentage"],
                    "hamming_dist": res["hamming_distance"],
                    "match": res["similarity_percentage"] >= threshold
                }
        return results
