"""
Sample Certificate Generator & Test Suite Builder
=================================================
Generates realistic high-quality synthetic academic certificates and simulated
real-world physical camera captures for all 8 test cases + quality failure tests.
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from config import SAMPLES_DIR


def get_font(size, bold=False):
    """Helper to load system TrueType fonts with default fallback."""
    try:
        font_names = [
            "timesbd.ttf" if bold else "times.ttf",
            "georgiab.ttf" if bold else "georgia.ttf",
            "arialbd.ttf" if bold else "arial.ttf"
        ]
        for fn in font_names:
            try:
                return ImageFont.truetype(fn, size)
            except Exception:
                continue
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


def create_base_certificate(
    university_name="OXFORD CAMBRIDGE INSTITUTE OF TECHNOLOGY",
    student_name="ALEXANDER M. MORGAN",
    degree="Bachelor of Science in Computer Science",
    honors="Summa Cum Laude",
    cert_no="CERT-8F31A2",
    date_str="JUNE 14, 2024",
    bg_color=(254, 252, 246),
    border_color=(28, 54, 98),
    gold_color=(198, 153, 47),
    seal_text="OFFICIAL SEAL • EXCELLENCE"
):
    """Draws a crisp, professional academic certificate using Pillow."""
    width, height = 1200, 840
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Outer Ornate Border
    draw.rectangle([20, 20, width - 20, height - 20], outline=border_color, width=6)
    draw.rectangle([28, 28, width - 28, height - 28], outline=gold_color, width=2)
    draw.rectangle([34, 34, width - 34, height - 34], outline=border_color, width=1)

    # Corner decorations
    for cx, cy in [(40, 40), (width - 40, 40), (40, height - 40), (width - 40, height - 40)]:
        draw.rectangle([cx - 10, cy - 10, cx + 10, cy + 10], fill=gold_color)
        draw.rectangle([cx - 6, cy - 6, cx + 6, cy + 6], fill=border_color)

    font_univ = get_font(34, bold=True)
    font_title = get_font(46, bold=True)
    font_body = get_font(20, bold=False)
    font_name = get_font(38, bold=True)
    font_degree = get_font(26, bold=True)
    font_meta = get_font(16, bold=False)

    # 2. University Header Banner
    draw.text((width // 2, 85), university_name, fill=border_color, font=font_univ, anchor="mm")
    draw.line([width // 2 - 280, 115, width // 2 + 280, 115], fill=gold_color, width=2)

    # 3. Certificate Title
    draw.text((width // 2, 170), "DIPLOMA OF GRADUATION", fill=gold_color, font=font_title, anchor="mm")
    draw.text((width // 2, 225), "THIS CERTIFIES THAT", fill=(80, 80, 80), font=font_body, anchor="mm")

    # 4. Student Name
    draw.text((width // 2, 280), student_name, fill=border_color, font=font_name, anchor="mm")
    draw.line([width // 2 - 250, 315, width // 2 + 250, 315], fill=(160, 160, 160), width=1)

    # 5. Conferral Body Text
    draw.text((width // 2, 360), "has successfully fulfilled all requirements and honors for the degree of", fill=(70, 70, 70), font=font_body, anchor="mm")
    draw.text((width // 2, 410), degree, fill=border_color, font=font_degree, anchor="mm")
    draw.text((width // 2, 455), f"with all honors, privileges, and rights thereto appertaining: {honors}", fill=(90, 90, 90), font=font_body, anchor="mm")

    # 6. Official Seal (Gold Circular Crest on Left)
    seal_center = (180, 640)
    draw.ellipse([seal_center[0] - 65, seal_center[1] - 65, seal_center[0] + 65, seal_center[1] + 65], fill=gold_color, outline=border_color, width=3)
    draw.ellipse([seal_center[0] - 52, seal_center[1] - 52, seal_center[0] + 52, seal_center[1] + 52], fill=(255, 248, 220), outline=gold_color, width=2)
    draw.text(seal_center, "SEAL\n1894", fill=border_color, font=font_degree, anchor="mm", align="center")

    # 7. Candidate Photo Box (Right side)
    photo_box = [width - 230, 560, width - 110, 720]
    draw.rectangle(photo_box, fill=(230, 235, 245), outline=border_color, width=2)
    draw.text(((photo_box[0] + photo_box[2]) // 2, (photo_box[1] + photo_box[3]) // 2), "STUDENT\nPHOTO", fill=(120, 130, 150), font=font_meta, anchor="mm", align="center")

    # 8. Signatures & Date (Center / Bottom)
    sig_y = 660
    # Left: President Signature
    draw.line([380, sig_y, 560, sig_y], fill=(50, 50, 50), width=2)
    draw.text((470, sig_y - 22), "J. R. Wellington", fill=(20, 40, 80), font=get_font(22, bold=True), anchor="mm")
    draw.text((470, sig_y + 18), "President of the Board", fill=(100, 100, 100), font=font_meta, anchor="mm")

    # Right: Academic Dean Signature
    draw.line([640, sig_y, 820, sig_y], fill=(50, 50, 50), width=2)
    draw.text((730, sig_y - 22), "Eleanor Vance, Ph.D.", fill=(20, 40, 80), font=get_font(22, bold=True), anchor="mm")
    draw.text((730, sig_y + 18), "Dean of Academic Affairs", fill=(100, 100, 100), font=font_meta, anchor="mm")

    # 9. Metadata Footer
    draw.text((width // 2, 770), f"Date of Conferral: {date_str}   |   Registration ID: {cert_no}", fill=(110, 110, 110), font=font_meta, anchor="mm")

    return img


def generate_all_samples():
    """Generates a complete suite of test images covering all 8 scenarios and quality failure cases."""
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    generated_files = {}

    print("Generating synthetic certificate test suite...")

    # 1. Base Original Certificate
    base_pil = create_base_certificate()
    orig_path = os.path.join(SAMPLES_DIR, "01_original_certificate.png")
    base_pil.save(orig_path, "PNG")
    generated_files["01_original"] = orig_path

    # Convert to OpenCV BGR
    orig_bgr = cv2.cvtColor(np.array(base_pil), cv2.COLOR_RGB2BGR)

    # 2. Resized Image (50% scale: 600x420)
    resized_bgr = cv2.resize(orig_bgr, (600, 420), interpolation=cv2.INTER_AREA)
    path_02 = os.path.join(SAMPLES_DIR, "02_resized_50pct.png")
    cv2.imwrite(path_02, resized_bgr)
    generated_files["02_resized"] = path_02

    # 3. JPEG Compressed Image (Quality 18)
    path_03 = os.path.join(SAMPLES_DIR, "03_compressed_jpeg.jpg")
    cv2.imwrite(path_03, orig_bgr, [cv2.IMWRITE_JPEG_QUALITY, 18])
    generated_files["03_compressed"] = path_03

    # 4. Photographed Physical Certificate on Wooden Desk (Perspective skew + lighting gradient)
    desk_h, desk_w = 1200, 1600
    # Create desk surface
    desk = np.full((desk_h, desk_w, 3), (45, 60, 85), dtype=np.uint8)  # Wood brown tone
    # Add wood grain texture noise
    noise = np.random.normal(0, 10, (desk_h, desk_w, 3)).astype(np.int16)
    desk = np.clip(desk.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Certificate quad points on desk (with 12-degree perspective tilt)
    src_pts = np.array([[0, 0], [1200, 0], [1200, 840], [0, 840]], dtype=np.float32)
    dst_pts = np.array([[220, 210], [1380, 140], [1440, 980], [160, 1020]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_cert = cv2.warpPerspective(orig_bgr, M, (desk_w, desk_h), borderValue=(0, 0, 0))

    # Mask for blending onto desk
    mask = cv2.warpPerspective(np.full((840, 1200), 255, dtype=np.uint8), M, (desk_w, desk_h))
    mask_3ch = cv2.merge([mask, mask, mask]) / 255.0

    # Add soft lighting vignette / smartphone camera gradient
    x = np.linspace(-1, 1, desk_w)
    y = np.linspace(-1, 1, desk_h)
    xx, yy = np.meshgrid(x, y)
    vignette = 1.0 - 0.25 * (xx**2 + yy**2)
    vignette_3ch = np.dstack([vignette, vignette, vignette])

    photo_sim = (warped_cert * mask_3ch + desk * (1.0 - mask_3ch)) * vignette_3ch
    photo_sim = np.clip(photo_sim, 0, 255).astype(np.uint8)

    path_04 = os.path.join(SAMPLES_DIR, "04_photograph_perspective.png")
    cv2.imwrite(path_04, photo_sim)
    generated_files["04_photo_perspective"] = path_04

    # 5. Grayscale Copy
    gray_cert = cv2.cvtColor(orig_bgr, cv2.COLOR_BGR2GRAY)
    path_05 = os.path.join(SAMPLES_DIR, "05_grayscale_scan.png")
    cv2.imwrite(path_05, gray_cert)
    generated_files["05_grayscale"] = path_05

    # 6. Varied Lighting (Warm 3200K tungsten lamp + slight brightness boost)
    warm_bgr = orig_bgr.astype(np.float32)
    warm_bgr[:, :, 0] *= 0.85  # Reduce Blue
    warm_bgr[:, :, 2] *= 1.15  # Boost Red
    warm_bgr = np.clip(warm_bgr + 15, 0, 255).astype(np.uint8)
    path_06 = os.path.join(SAMPLES_DIR, "06_warm_lighting.png")
    cv2.imwrite(path_06, warm_bgr)
    generated_files["06_warm_lighting"] = path_06

    # 7. Modified Certificate (Tampered Student Name & Reg Number)
    tampered_pil = create_base_certificate(
        student_name="VICTORIA R. STERLING",
        degree="Bachelor of Science in Computer Science",
        cert_no="CERT-9X82B1"
    )
    path_07 = os.path.join(SAMPLES_DIR, "07_tampered_name.png")
    tampered_pil.save(path_07, "PNG")
    generated_files["07_tampered_name"] = path_07

    # 8. Completely Different University Certificate (Distinct Layout & Colors)
    diff_img = Image.new("RGB", (1200, 840), (255, 255, 255))
    diff_draw = ImageDraw.Draw(diff_img)

    # Dark Green Top Banner
    diff_draw.rectangle([0, 0, 1200, 150], fill=(20, 75, 45))
    diff_draw.rectangle([0, 145, 1200, 152], fill=(210, 175, 55))
    diff_draw.text((600, 65), "METROPOLITAN UNIVERSITY OF TECHNOLOGY", fill=(255, 255, 255), font=get_font(32, bold=True), anchor="mm")
    diff_draw.text((600, 105), "FACULTY OF ENGINEERING & APPLIED SCIENCES", fill=(200, 230, 210), font=get_font(18, bold=False), anchor="mm")

    # Center Watermark Crest
    diff_draw.ellipse([450, 270, 750, 570], outline=(220, 240, 230), width=6)
    diff_draw.text((600, 420), "MUT", fill=(220, 240, 230), font=get_font(60, bold=True), anchor="mm")

    # Degree Content
    diff_draw.text((600, 230), "BY AUTHORITY OF THE BOARD OF TRUSTEES", fill=(100, 100, 100), font=get_font(16), anchor="mm")
    diff_draw.text((600, 310), "DOCTOR OF MEDICINE", fill=(20, 75, 45), font=get_font(38, bold=True), anchor="mm")
    diff_draw.text((600, 370), "CONFIRMED UPON", fill=(100, 100, 100), font=get_font(16), anchor="mm")
    diff_draw.text((600, 440), "DR. EMILY CLAIRE WATSON", fill=(20, 20, 20), font=get_font(32, bold=True), anchor="mm")
    diff_draw.text((600, 500), "for distinguished research in biomedical engineering and clinical neurology.", fill=(80, 80, 80), font=get_font(18), anchor="mm")

    # 3-Column Footer Signatures
    diff_draw.line([120, 680, 360, 680], fill=(60, 60, 60), width=2)
    diff_draw.text((240, 705), "Chancellor", fill=(100, 100, 100), font=get_font(15), anchor="mm")

    diff_draw.line([480, 680, 720, 680], fill=(60, 60, 60), width=2)
    diff_draw.text((600, 705), "Dean of Faculty", fill=(100, 100, 100), font=get_font(15), anchor="mm")

    diff_draw.line([840, 680, 1080, 680], fill=(60, 60, 60), width=2)
    diff_draw.text((960, 705), "Secretary of Senate", fill=(100, 100, 100), font=get_font(15), anchor="mm")

    diff_draw.text((600, 780), "MUT-REG-99410 • CONFERRED AUGUST 2024", fill=(140, 140, 140), font=get_font(14), anchor="mm")

    path_08 = os.path.join(SAMPLES_DIR, "08_different_certificate.png")
    diff_img.save(path_08, "PNG")
    generated_files["08_different_cert"] = path_08

    # 9. Quality Failure: Too Blurry (Laplacian Variance < 90)
    blurry_bgr = cv2.GaussianBlur(orig_bgr, (25, 25), 0)
    path_09 = os.path.join(SAMPLES_DIR, "09_quality_fail_blurry.png")
    cv2.imwrite(path_09, blurry_bgr)
    generated_files["09_fail_blurry"] = path_09

    # 10. Quality Failure: Too Dark (Mean Brightness < 40)
    dark_bgr = np.clip(orig_bgr.astype(np.float32) * 0.12, 0, 255).astype(np.uint8)
    path_10 = os.path.join(SAMPLES_DIR, "10_quality_fail_dark.png")
    cv2.imwrite(path_10, dark_bgr)
    generated_files["10_fail_dark"] = path_10

    # 11. Quality Failure: Extreme 55° Perspective Skew (Acute keystone angle)
    dst_extreme = np.array([[550, 450], [1500, 200], [1050, 1150], [80, 850]], dtype=np.float32)
    M_extreme = cv2.getPerspectiveTransform(src_pts, dst_extreme)
    extreme_skew = cv2.warpPerspective(orig_bgr, M_extreme, (desk_w, desk_h), borderValue=(30, 30, 30))
    path_11 = os.path.join(SAMPLES_DIR, "11_quality_fail_extreme_angle.png")
    cv2.imwrite(path_11, extreme_skew)
    generated_files["11_fail_extreme_angle"] = path_11

    print(f"Successfully generated {len(generated_files)} sample test certificates in {SAMPLES_DIR}")
    return generated_files


if __name__ == "__main__":
    generate_all_samples()
