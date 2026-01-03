import base64
import json
import requests
import os
import io
from pdf2image import convert_from_path
from PIL import Image

from beautifyText import beautify_academic_document
from verify_college import attach_verification, add_verification_summary
from consistency_check import consistency_check

# =========================
# CONFIG
# =========================
API_KEY = "AIzaSyCZbt5DhxYl7tn6SFLdmURz_cZJwi4C1mI"
VISION_URL = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"

# =========================
# HELPERS
# =========================
def pil_to_base64(image: Image.Image) -> str:
    if image.mode == "RGBA":
        image = image.convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    images = []

    if ext == ".pdf":
        images = convert_from_path(
            file_path, dpi=300, poppler_path=POPPLER_PATH
        )
    elif ext in [".jpg", ".jpeg", ".png"]:
        images = [Image.open(file_path)]
    else:
        raise ValueError("Unsupported file type")

    full_text = ""

    for img in images:
        payload = {
            "requests": [{
                "image": {"content": pil_to_base64(img)},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
            }]
        }

        res = requests.post(VISION_URL, json=payload)
        res.raise_for_status()

        text = res.json()["responses"][0].get(
            "fullTextAnnotation", {}
        ).get("text", "")

        full_text += text + "\n"

    return full_text.strip()


def detect_digilocker(ocr_text: str) -> bool:
    keywords = [
        "digilocker",
        "national academic depository",
        "digitally signed",
        "it act 2000"
    ]
    text = ocr_text.lower()
    return any(k in text for k in keywords)

# =========================
# MAIN PIPELINE
# =========================
def process_certificates(file_paths: list) -> dict:
    all_certificates = []

    for path in file_paths:
        ocr_text = extract_text(path)

        structured = beautify_academic_document(ocr_text)
        verified = attach_verification(structured)
        verified = add_verification_summary(verified)

        # DigiLocker boost
        if detect_digilocker(ocr_text):
            verified["verification_summary"]["digilocker_verified"] = True
            verified["confidence_score"] = min(
                verified.get("confidence_score", 0.7) + 0.05, 1.0
            )

        all_certificates.append(verified)

    # Cross-certificate consistency
    consistency = consistency_check(all_certificates)

    final_profile = {
        "certificates": all_certificates,
        "cross_certificate_consistency": consistency,
        "final_risk_level": "HIGH" if consistency["risk_level"] == "HIGH" else "LOW"
    }

    if consistency["risk_level"] == "HIGH":
        for cert in final_profile["certificates"]:
            cert["fraud_checks"]["risk_level"] = "HIGH"
            cert["confidence_score"] -= 0.2

    return final_profile

# =========================
# RUN
# =========================
if __name__ == "__main__":
    files = [
        "TextExtraction/atharva.jpeg",
        # "TextExtraction/class10.pdf",
        # "TextExtraction/degree.pdf"
    ]

    output = process_certificates(files)
    print(json.dumps(output, indent=2))
