import os
import io
import base64
import json
import requests
from collections import Counter
from typing import List, Dict

import pdfplumber
from pdf2image import convert_from_path
from PIL import Image

# ================== CONFIG ==================
API_KEY = "AIzaSyCZbt5DhxYl7tn6SFLdmURz_cZJwi4C1mI"
VISION_URL = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
# ============================================


# ---------- UTILS ----------
def pil_to_base64(image: Image.Image) -> str:
    if image.mode != "RGB":
        image = image.convert("RGB")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()


# ---------- 1. DIGITAL PDF FONT METADATA ----------
def extract_pdf_font_metadata(pdf_path: str) -> List[Dict]:
    fonts = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            for char in page.chars:
                if char["text"].strip():
                    fonts.append({
                        "page": page_no,
                        "text": char["text"],
                        "font_name": char["fontname"],
                        "font_size": round(char["size"], 2)
                    })

    return fonts


def analyze_pdf_font_consistency(fonts: List[Dict]) -> Dict:
    pairs = [(f["font_name"], f["font_size"]) for f in fonts]
    counter = Counter(pairs)

    dominant, dominant_count = counter.most_common(1)[0]
    inconsistency_ratio = 1 - (dominant_count / len(pairs))

    return {
        "method": "PDF Font Metadata",
        "dominant_font": dominant[0],
        "dominant_size": dominant[1],
        "inconsistency_ratio": round(inconsistency_ratio, 3),
        "is_suspicious": inconsistency_ratio > 0.15
    }


# ---------- 2. OCR FONT CONSISTENCY (SCANNED DOCS) ----------
def extract_ocr_font_metrics(file_path: str) -> List[Dict]:
    ext = os.path.splitext(file_path)[1].lower()
    images = []

    if ext == ".pdf":
        images = convert_from_path(
            file_path, dpi=300, poppler_path=POPPLER_PATH
        )
    else:
        images.append(Image.open(file_path))

    metrics = []

    for img in images:
        payload = {
            "requests": [{
                "image": {"content": pil_to_base64(img)},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
            }]
        }

        res = requests.post(VISION_URL, json=payload).json()
        annotations = res["responses"][0].get("textAnnotations", [])

        for a in annotations[1:]:
            vertices = a["boundingPoly"]["vertices"]
            if "y" in vertices[0] and "y" in vertices[2]:
                height = abs(vertices[0]["y"] - vertices[2]["y"])
                metrics.append({
                    "text": a["description"],
                    "approx_font_height": height
                })

    return metrics


def analyze_ocr_font_consistency(metrics: List[Dict]) -> Dict:
    heights = [m["approx_font_height"] for m in metrics if m["approx_font_height"] > 0]
    if not heights:
        return {"method": "OCR Font Analysis", "is_suspicious": False}

    avg = sum(heights) / len(heights)
    anomalies = [h for h in heights if abs(h - avg) > avg * 0.35]

    return {
        "method": "OCR Font Consistency",
        "average_height": round(avg, 2),
        "anomaly_ratio": round(len(anomalies) / len(heights), 2),
        "is_suspicious": len(anomalies) > len(heights) * 0.25
    }


# ---------- 3. FINAL FORGERY REPORT ----------
def generate_forgery_report(pdf_result=None, ocr_result=None) -> Dict:
    score = 0
    reasons = []

    if pdf_result and pdf_result.get("is_suspicious"):
        score += 40
        reasons.append("Multiple font styles detected in digital PDF")

    if ocr_result and ocr_result.get("is_suspicious"):
        score += 30
        reasons.append("Inconsistent font sizing detected via OCR")

    verdict = (
        "HIGH RISK" if score >= 60
        else "MEDIUM RISK" if score >= 30
        else "LOW RISK"
    )

    return {
        "forgery_risk_score": score,
        "verdict": verdict,
        "reasons": reasons
    }


# ---------- MAIN ENTRY ----------
def analyze_certificate(file_path: str) -> Dict:
    report = {"file": os.path.basename(file_path)}

    try:
        pdf_fonts = extract_pdf_font_metadata(file_path)
        if pdf_fonts:
            report["pdf_font_analysis"] = analyze_pdf_font_consistency(pdf_fonts)
    except:
        pass  # not a digital PDF

    ocr_metrics = extract_ocr_font_metrics(file_path)
    report["ocr_font_analysis"] = analyze_ocr_font_consistency(ocr_metrics)

    report["final_verdict"] = generate_forgery_report(
        report.get("pdf_font_analysis"),
        report.get("ocr_font_analysis")
    )

    return report


# ---------- RUN ----------
if __name__ == "__main__":
    FILE_PATH = "SampleImage/degree.pdf"  # pdf / jpg / png

    result = analyze_certificate(FILE_PATH)
    print(json.dumps(result, indent=2))
