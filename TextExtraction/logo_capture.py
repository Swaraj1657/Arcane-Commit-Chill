import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
import os

def load_document(path):
    if path.lower().endswith(".pdf"):
        pages = convert_from_path(path, dpi=300)
        image = np.array(pages[0])
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    else:
        image = cv2.imread(path)

    if image is None:
        raise ValueError("Invalid file or path")

    return image


def extract_logo_v2(image, save_path="extracted_logo.png", debug=False):
    h, w, _ = image.shape

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 1️⃣ Contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 2️⃣ Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31, 5
    )

    # 3️⃣ MSER (CORRECT WAY)
    mser = cv2.MSER_create()
    mser.setMinArea(int(0.002 * h * w))
    mser.setMaxArea(int(0.12 * h * w))

    regions, _ = mser.detectRegions(gray)

    candidates = []

    for region in regions:
        x, y, cw, ch = cv2.boundingRect(region)
        area = cw * ch
        aspect = cw / float(ch)

        if (
            0.03 * w < cw < 0.4 * w and
            0.03 * h < ch < 0.4 * h and
            0.5 < aspect < 4.0 and
            y < 0.4 * h
        ):
            edge_density = np.mean(thresh[y:y+ch, x:x+cw] > 0)
            score = area * edge_density
            candidates.append((score, x, y, cw, ch))

    if not candidates:
        return None

    # Best candidate
    _, x, y, cw, ch = max(candidates, key=lambda x: x[0])

    logo = image[y:y+ch, x:x+cw]
    cv2.imwrite(save_path, logo)

    if debug:
        dbg = image.copy()
        cv2.rectangle(dbg, (x, y), (x+cw, y+ch), (0, 255, 0), 2)
        cv2.imwrite("debug_logo_box.png", dbg)

    return {
        "logo_path": save_path,
        "bbox": [int(x), int(y), int(cw), int(ch)]
    }




doc = load_document("SY_marksheet.pdf")
result = extract_logo_v2(doc)

if result:
    print("Logo extracted:", result)
else:
    print("Logo not found")