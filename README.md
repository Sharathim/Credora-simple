# Academic Certificate Perceptual Image Verification Demo

> **A web application for testing whether physical hard-copy academic certificates (photographed with a smartphone or scanned) can be verified against an authorized issuer's original digital certificate using OpenCV Quality Gates, 4-Point Perspective Transform, and Perceptual Image Hashing (pHash).**

---

## 🌟 Application Structure

The application provides two clear sections:

### A. Issuer Upload
1. **Upload Original**: The authorized issuer uploads the original digital certificate.
2. **Quality Check**: The system automatically validates resolution, sharpness (Laplacian variance), brightness, contrast, and document boundaries. If any quality test fails, the upload is rejected with a clear explanation.
3. **Preprocessing & Fingerprinting**: If quality passes, the document is normalized and a perceptual image fingerprint (`pHash`) is generated.
4. **Certificate ID**: The fingerprint is stored locally in SQLite and a unique **Certificate ID** (e.g. `CERT-8F31A2`) is generated.

### B. Verify Certificate
1. **Verifier Upload**: The verifier uploads a photograph or scan of the physical certificate and enters the Certificate ID.
2. **Quality Gate**: The system checks image quality first (rejecting blurry, badly angled, poorly lit, or cropped images).
3. **Auto Perspective Correction**: Skewed photographs with desk backgrounds are automatically detected and rectified via 4-point homography transform.
4. **Perceptual Matching**: The uploaded copy's perceptual hash is computed and compared with the issuer's stored hash using Hamming distance.
5. **Clear Results**: Displays a similarity score and MATCH / MISMATCH badge with side-by-side visual comparison.

---

## 🚀 How to Run

### 1. Virtual Environment Setup
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies inside venv
pip install -r requirements.txt
```

### 2. Start the Application
```powershell
.\venv\Scripts\python.exe app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📂 Project Structure

```
d:/Credora/Credora/
├── app.py                      # Flask REST API & Web Server
├── config.py                   # Centralized configuration & thresholds
├── requirements.txt            # Python dependencies (Flask, OpenCV, Pillow, ImageHash, NumPy)
├── venv/                       # Dedicated Python virtual environment
├── core/
│   ├── quality_checker.py      # Laplacian blur, brightness, contrast, resolution, skew checks
│   ├── preprocessor.py         # 4-point perspective warp, rotation alignment & normalization
│   ├── perceptual_hasher.py    # pHash (DCT), dHash, aHash, wHash, Hamming distance & RegionHasher
│   └── database.py             # SQLite storage for certificate IDs and visual fingerprints
├── templates/
│   └── index.html              # Clean single-page application
├── static/
│   ├── css/style.css           # Modern styling, responsive side-by-side viewer
│   └── js/app.js               # Upload handling, pipeline progress animation, threshold slider
└── storage/
    ├── uploads/                # Issuer master images
    ├── processed/              # Preprocessed canonical images
    └── certificates.db         # Local SQLite database
```

---

## 🛡️ Image Quality Gates

Before computing any hashes, uploaded certificates must pass 6 automated OpenCV quality gates:
- **Blur / Sharpness**: Laplacian variance threshold ($\text{Var}(\nabla^2 I) \ge 80.0$).
- **Brightness**: Mean pixel luminance between $35$ and $248$.
- **Contrast**: Grayscale luminance standard deviation $\ge 25.0$.
- **Resolution**: Minimum dimensions $500 \times 350\text{ px}$.
- **Document Visibility**: Certificate area occupies $\ge 18\%$ of image frame.
- **Perspective Skew**: Max quadrilateral angle $\le 45^\circ$. Angles between $8^\circ$ and $45^\circ$ are automatically corrected via perspective warp.

---

## 🔒 Security Note (Prototype Scope)

> **Important**: Perceptual hashing specifically measures **visual structural similarity**. In a production deployment, perceptual hashing should be combined with:
> **Issuer Identity & Signatures + Certificate ID + Cryptographic Integrity + OCR / Text Verification + Access Control & Audit Trails.**
