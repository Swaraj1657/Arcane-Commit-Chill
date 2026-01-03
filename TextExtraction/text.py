import base64
import json
import requests
import os
import io
from pdf2image import convert_from_path
from PIL import Image

from beautifyText import beautify_academic_document

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
        pages = convert_from_path(
            file_path,
            dpi=300,
            poppler_path=POPPLER_PATH
        )
        images.extend(pages)

    elif ext in [".jpg", ".jpeg", ".png"]:
        images.append(Image.open(file_path))

    else:
        raise ValueError("Unsupported file type")

    extracted_text = ""

    for img in images:
        img_base64 = pil_to_base64(img)

        payload = {
            "requests": [
                {
                    "image": {"content": img_base64},
                    "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
                }
            ]
        }

        response = requests.post(VISION_URL, json=payload)
        response.raise_for_status()

        result = response.json()
        text = result["responses"][0].get(
            "fullTextAnnotation", {}
        ).get("text", "")

        extracted_text += text + "\n"

    return extracted_text.strip()


if __name__ == "__main__":
    text = beautify_academic_document(extract_text(".\TextExtraction\class10.pdf"))# or .pdf
    
    print(json.dumps(text, indent=2))

from verify_college import attach_verification,add_verification_summary


structured = beautify_academic_document(text)
verified = attach_verification(structured)
final_output = add_verification_summary(verified)

print(json.dumps(final_output, indent=2))
