"""
Academic Certificate Perceptual Image Verification - Web Application
====================================================================
Flask Server providing Issuer & Verifier REST APIs and UI dashboard.
"""

import os
import time
import json
import cv2
import numpy as np
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

from config import (
    UPLOAD_DIR,
    PROCESSED_DIR,
    MATCH_THRESHOLD,
    PHASH_SIZE
)
from core.quality_checker import QualityChecker
from core.preprocessor import ImagePreprocessor
from core.perceptual_hasher import PerceptualHasher, RegionHasher
from core.database import Database

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Initialize core services
quality_checker = QualityChecker()
preprocessor = ImagePreprocessor()
hasher = PerceptualHasher(hash_size=PHASH_SIZE)
region_hasher = RegionHasher(hasher)
db = Database()


def decode_image(file_storage_or_bytes):
    """Decodes uploaded file bytes to an OpenCV BGR NumPy array."""
    if hasattr(file_storage_or_bytes, "read"):
        file_bytes = file_storage_or_bytes.read()
    else:
        file_bytes = file_storage_or_bytes
    nparr = np.frombuffer(file_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image


@app.route("/")
def index():
    """Renders the main single-page verification dashboard."""
    return render_template("index.html")


@app.route("/api/certificates", methods=["GET"])
def list_certificates():
    """Returns recently registered issuer certificates."""
    certs = db.list_certificates(limit=20)
    return jsonify({"success": True, "certificates": certs})


@app.route("/api/issuer/upload", methods=["POST"])
def issuer_upload():
    """
    Issuer Upload Endpoint:
    1. Inspects image quality.
    2. Rejects if failing quality criteria.
    3. Preprocesses (perspective correction, rotation, normalization, resizing).
    4. Computes perceptual visual hashes (pHash, dHash, aHash, wHash).
    5. Saves record to SQLite with unique Certificate ID (e.g. CERT-8F31A2).
    """
    image_file = request.files.get("image")

    if not image_file or not image_file.filename:
        return jsonify({"success": False, "message": "No certificate image file uploaded."}), 400

    orig_filename = image_file.filename
    image_np = decode_image(image_file)

    if image_np is None:
        return jsonify({"success": False, "message": "Failed to decode image file. Please upload a valid PNG/JPEG."}), 400

    # Step 1: Quality Check
    quality_report = quality_checker.inspect(image_np)
    if not quality_report["passed"]:
        return jsonify({
            "success": False,
            "stage": "quality_check",
            "quality_report": quality_report,
            "message": quality_report["summary"]
        }), 422

    # Step 2: Preprocess Certificate
    try:
        prep_res = preprocessor.preprocess(image_np, corners=quality_report.get("detected_corners"))
        canonical_gray = prep_res["gray_canonical"]
        canonical_color = prep_res["color_canonical"]
    except Exception as e:
        return jsonify({"success": False, "message": f"Preprocessing error: {str(e)}"}), 500

    # Step 3: Compute Perceptual Hashes
    hashes = hasher.compute_all_hashes(canonical_gray)
    region_hashes = region_hasher.compute_region_hashes(canonical_gray)

    # Step 4: Generate unique Certificate ID and save
    cert_id = db.generate_cert_id()
    orig_saved_name = f"{cert_id}_original_{int(time.time())}.png"
    proc_saved_name = f"{cert_id}_canonical_{int(time.time())}.png"

    orig_saved_path = os.path.join(UPLOAD_DIR, orig_saved_name)
    proc_saved_path = os.path.join(PROCESSED_DIR, proc_saved_name)

    cv2.imwrite(orig_saved_path, image_np)
    cv2.imwrite(proc_saved_path, canonical_color)

    metadata = {
        "student_name": request.form.get("student_name", "").strip(),
        "university": request.form.get("university", "").strip(),
        "degree": request.form.get("degree", "").strip(),
        "issue_date": request.form.get("issue_date", "").strip()
    }

    db.save_certificate(
        cert_id=cert_id,
        original_filename=orig_filename,
        original_image_path=orig_saved_name,
        preprocessed_image_path=proc_saved_name,
        hashes=hashes,
        region_hashes=region_hashes,
        quality_report=quality_report,
        metadata=metadata
    )

    return jsonify({
        "success": True,
        "cert_id": cert_id,
        "message": "Certificate registered successfully.",
        "quality_report": quality_report,
        "original_image_url": f"/storage/uploads/{orig_saved_name}",
        "preprocessed_image_url": f"/storage/processed/{proc_saved_name}",
        "metadata": metadata
    })


@app.route("/api/verifier/verify", methods=["POST"])
def verifier_verify():
    """
    Verifier Endpoint:
    1. Inspects image quality first.
    2. Rejects if quality check fails with detailed explanation.
    3. Preprocesses verifier image (perspective correction, cropping, normalization).
    4. Computes perceptual visual hash.
    5. Retrieves issuer original from database by Certificate ID.
    6. Calculates Hamming distance & similarity score against MATCH_THRESHOLD.
    7. Returns complete visual verification comparison report.
    """
    cert_id = request.form.get("cert_id", "").strip().upper()
    threshold = float(request.form.get("threshold", MATCH_THRESHOLD))
    image_file = request.files.get("image")

    if not cert_id:
        return jsonify({"success": False, "message": "Certificate ID is required."}), 400

    # Retrieve issuer record
    issuer_record = db.get_certificate(cert_id)
    if not issuer_record:
        return jsonify({
            "success": False,
            "message": f"Certificate ID '{cert_id}' not found in the issuer registry. Please verify the ID."
        }), 404

    # Decode image
    if not image_file or not image_file.filename:
        return jsonify({"success": False, "message": "No verification image uploaded."}), 400

    image_np = decode_image(image_file)
    if image_np is None:
        return jsonify({"success": False, "message": "Failed to decode uploaded image file."}), 400

    # Step 1: Quality Inspection
    quality_report = quality_checker.inspect(image_np)
    if not quality_report["passed"]:
        return jsonify({
            "success": False,
            "stage": "quality_check",
            "quality_report": quality_report,
            "message": quality_report["summary"]
        }), 422

    # Step 2: Preprocess Verification Image
    try:
        prep_res = preprocessor.preprocess(image_np, corners=quality_report.get("detected_corners"))
        canonical_gray = prep_res["gray_canonical"]
        canonical_color = prep_res["color_canonical"]
    except Exception as e:
        return jsonify({"success": False, "message": f"Preprocessing error: {str(e)}"}), 500

    # Save verifier preprocessed image for UI side-by-side display
    verifier_saved_name = f"verify_{cert_id}_{int(time.time())}.png"
    verifier_saved_path = os.path.join(PROCESSED_DIR, verifier_saved_name)
    cv2.imwrite(verifier_saved_path, canonical_color)

    # Step 3: Compute Hashes
    verifier_hashes = hasher.compute_all_hashes(canonical_gray)

    # Step 4: Compare with Issuer Original
    issuer_hashes = {
        "phash": issuer_record["phash"],
        "dhash": issuer_record["dhash"],
        "ahash": issuer_record["ahash"],
        "whash": issuer_record["whash"]
    }

    eval_result = hasher.evaluate_verification(issuer_hashes, verifier_hashes, threshold=threshold)

    return jsonify({
        "success": True,
        "cert_id": cert_id,
        "decision": eval_result["decision"],
        "is_match": eval_result["is_match"],
        "similarity_percentage": eval_result["primary_similarity"],
        "hamming_distance": eval_result["hamming_distance"],
        "threshold_used": threshold,
        "status_text": eval_result["status_text"],
        "hash_breakdown": eval_result["hash_breakdown"],
        "quality_report": quality_report,
        "preprocessing_info": {
            "perspective_corrected": prep_res["perspective_corrected"],
            "rotation_applied": prep_res["rotation_applied"]
        },
        "issuer_original_url": f"/storage/processed/{issuer_record['preprocessed_image_path']}",
        "verifier_processed_url": f"/storage/processed/{verifier_saved_name}",
        "issuer_metadata": issuer_record.get("metadata", {})
    })


@app.route("/storage/uploads/<filename>")
def serve_upload(filename):
    """Serves raw uploaded images."""
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/storage/processed/<filename>")
def serve_processed(filename):
    """Serves preprocessed canonical certificate images."""
    return send_from_directory(PROCESSED_DIR, filename)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Academic Certificate Perceptual Verification Server")
    print("  Running on: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
