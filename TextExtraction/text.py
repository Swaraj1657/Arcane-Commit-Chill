import base64
import json
import requests
import os
import io
from pdf2image import convert_from_path
from PIL import Image

from beautifyText import beautify_academic_document
from verify_college import attach_verification, add_verification_summary

API_KEY = "AIzaSyCZbt5DhxYl7tn6SFLdmURz_cZJwi4C1mI"
VISION_URL = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"

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
        images = convert_from_path(file_path, dpi=300, poppler_path=POPPLER_PATH)
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

# =========================
# RUN
# =========================
if __name__ == "__main__":
    ocr_text = extract_text("TextExtraction/certificate.png")
    structured = beautify_academic_document(ocr_text)

    verified = attach_verification(structured)
    final_output = add_verification_summary(verified)

    print(json.dumps(final_output, indent=2))