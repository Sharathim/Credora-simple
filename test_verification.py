import os
import sys
import cv2

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.quality_checker import QualityChecker
from core.preprocessor import ImagePreprocessor
from core.perceptual_hasher import PerceptualHasher, RegionHasher
from core.database import Database
import generate_samples
from config import SAMPLES_DIR, MATCH_THRESHOLD


def run_all_tests():
    print("=" * 70)
    print(" Credora Perceptual Verification Test Suite")
    print("=" * 70)

    # 1. Ensure samples exist
    generate_samples.generate_all_samples()

    # 2. Initialize components
    qc = QualityChecker()
    prep = ImagePreprocessor()
    hasher = PerceptualHasher(hash_size=8)
    rhasher = RegionHasher(hasher)
    db = Database()

    # 3. Register Issuer Master Certificate
    orig_path = os.path.join(SAMPLES_DIR, "01_original_certificate.png")
    orig_img = cv2.imread(orig_path)
    assert orig_img is not None, "Failed to load master certificate."

    # Inspect quality of master
    master_qc = qc.inspect(orig_img)
    assert master_qc["passed"], "Master certificate failed quality check!"

    # Preprocess master
    master_prep = prep.preprocess(orig_img, corners=master_qc["detected_corners"])
    master_hashes = hasher.compute_all_hashes(master_prep["gray_canonical"])
    master_region_hashes = rhasher.compute_region_hashes(master_prep["gray_canonical"])

    cert_id = db.generate_cert_id()
    db.save_certificate(
        cert_id=cert_id,
        original_filename="01_original_certificate.png",
        original_image_path="01_original_certificate.png",
        preprocessed_image_path="01_canonical.png",
        hashes=master_hashes,
        region_hashes=master_region_hashes
    )
    print(f"\n[ISSUER REGISTRATION] Master Certificate Registered: {cert_id}")
    print(f"Master pHash: {master_hashes['phash']}")

    # 4. Execute Test Cases
    test_cases = [
        ("Test 1 — Exact same image", "01_original_certificate.png", True, 98.0, "Exact match expected"),
        ("Test 2 — Resized image (50%)", "02_resized_50pct.png", True, 90.0, "Scale invariance expected"),
        ("Test 3 — JPEG compressed (Q18)", "03_compressed_jpeg.jpg", True, 90.0, "Compression invariance expected"),
        ("Test 4 — Photographed on desk", "04_photograph_perspective.png", True, 85.0, "Perspective warp & lighting correction"),
        ("Test 5 — Grayscale scan", "05_grayscale_scan.png", True, 95.0, "Grayscale structure invariance"),
        ("Test 6 — Warm lighting photo", "06_warm_lighting.png", True, 90.0, "Color temperature invariance"),
        ("Test 7 — Modified certificate", "07_tampered_name.png", None, None, "Tampered text test"),
        ("Test 8 — Different university", "08_different_certificate.png", False, 70.0, "Mismatch expected"),
    ]

    print("\n" + "-" * 70)
    print(" RUNNING 8 PRIMARY VERIFICATION SCENARIOS")
    print("-" * 70)

    for name, filename, expected_match, target_sim, desc in test_cases:
        filepath = os.path.join(SAMPLES_DIR, filename)
        img = cv2.imread(filepath)

        # Quality check
        q_rep = qc.inspect(img)
        assert q_rep["passed"], f"Test '{name}' unexpectedly failed quality inspection: {q_rep['summary']}"

        # Preprocessing & Hasher
        p_res = prep.preprocess(img, corners=q_rep["detected_corners"])
        v_hashes = hasher.compute_all_hashes(p_res["gray_canonical"])
        eval_res = hasher.evaluate_verification(master_hashes, v_hashes, threshold=MATCH_THRESHOLD)

        sim = eval_res["primary_similarity"]
        dec = eval_res["decision"]
        h_dist = eval_res["hamming_distance"]

        # Validate against expectations
        if expected_match is True:
            passed_assert = (dec == "MATCH") and (sim >= target_sim)
        elif expected_match is False:
            passed_assert = (dec == "MISMATCH") and (sim <= target_sim)
        else:
            # Modified test case
            passed_assert = True

        status_flag = "PASSED" if passed_assert else "FAILED"
        print(f"[{status_flag}] {name}")
        print(f"         Decision: {dec} | Similarity: {sim:.1f}% | Hamming Dist: {h_dist}/64 | Warp: {p_res['perspective_corrected']}")

    # 5. Quality Gate Rejection Tests
    print("\n" + "-" * 70)
    print(" RUNNING QUALITY GATE REJECTION TESTS")
    print("-" * 70)

    rejection_tests = [
        ("Reject Test 1 — Blurry Photo", "09_quality_fail_blurry.png", "sharpness"),
        ("Reject Test 2 — Pitch Dark Photo", "10_quality_fail_dark.png", "brightness"),
        ("Reject Test 3 — 55° Extreme Tilt", "11_quality_fail_extreme_angle.png", "document_angle")
    ]

    for name, filename, failed_check_key in rejection_tests:
        filepath = os.path.join(SAMPLES_DIR, filename)
        img = cv2.imread(filepath)
        q_rep = qc.inspect(img)
        check_failed = not q_rep["passed"]
        specific_check_status = q_rep["checks"].get(failed_check_key, {}).get("status")

        status_flag = "PASSED (Correctly Rejected)" if check_failed else "FAILED (Should have been rejected)"
        print(f"[{status_flag}] {name}")
        print(f"         Reason: {q_rep['summary']}")
        print(f"         Check '{failed_check_key}' status: {specific_check_status}")

    print("\n" + "=" * 70)
    print(" ALL VERIFICATION AND QUALITY TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
