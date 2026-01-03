import os
import cv2
import numpy as np
from PIL import Image

# =========================
# OPTIONAL CLIP IMPORT
# =========================
try:
    import torch
    import clip

    device = "cuda" if torch.cuda.is_available() else "cpu"
    clip_model, clip_preprocess = clip.load("ViT-B/32", device=device)
    CLIP_AVAILABLE = True
except Exception as e:
    CLIP_AVAILABLE = False


#################################
# CLIP SIMILARITY
#################################
def clip_similarity(img1_path, img2_path):
    img1 = clip_preprocess(
        Image.open(img1_path).convert("RGB")
    ).unsqueeze(0).to(device)

    img2 = clip_preprocess(
        Image.open(img2_path).convert("RGB")
    ).unsqueeze(0).to(device)

    with torch.no_grad():
        f1 = clip_model.encode_image(img1)
        f2 = clip_model.encode_image(img2)

    f1 /= f1.norm(dim=-1, keepdim=True)
    f2 /= f2.norm(dim=-1, keepdim=True)

    return torch.cosine_similarity(f1, f2).item()


#################################
# ORB FALLBACK VERIFIER
#################################
def orb_verify(reference_logo_path, cropped_logo_path,
               min_good_matches=10, threshold=0.12):

    logo = cv2.imread(reference_logo_path, cv2.IMREAD_GRAYSCALE)
    crop = cv2.imread(cropped_logo_path, cv2.IMREAD_GRAYSCALE)

    if logo is None or crop is None:
        return False, 0.0

    orb = cv2.ORB_create(nfeatures=3000)
    kp1, des1 = orb.detectAndCompute(logo, None)
    kp2, des2 = orb.detectAndCompute(crop, None)

    if des1 is None or des2 is None:
        return False, 0.0

    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = bf.knnMatch(des1, des2, k=2)

    good = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good.append(m)

    if len(good) < min_good_matches:
        return False, 0.0

    src_pts = np.float32(
        [kp1[m.queryIdx].pt for m in good]
    ).reshape(-1, 1, 2)

    dst_pts = np.float32(
        [kp2[m.trainIdx].pt for m in good]
    ).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    if H is None:
        return False, 0.0

    inliers = int(mask.sum())
    score = inliers / max(len(kp1), 1)

    return score >= threshold, round(score, 3)


#################################
# FINAL HYBRID VERIFIER (SAFE)
#################################
def verify_logo_hybrid(reference_logo, cropped_logo):
    """
    Safe logo verification.
    Never crashes if files / CLIP missing.
    """

    if not os.path.exists(reference_logo):
        return {
            "verified": False,
            "method": "SKIPPED",
            "reason": "Reference logo not found"
        }

    if not os.path.exists(cropped_logo):
        return {
            "verified": False,
            "method": "SKIPPED",
            "reason": "Extracted logo not found"
        }

    # 1️⃣ CLIP (if available)
    if CLIP_AVAILABLE:
        try:
            clip_score = clip_similarity(reference_logo, cropped_logo)

            if clip_score >= 0.80:
                return {
                    "verified": True,
                    "method": "CLIP",
                    "clip_score": round(clip_score, 3)
                }
        except Exception:
            pass  # silently fallback to ORB

    # 2️⃣ ORB fallback
    orb_ok, orb_score = orb_verify(reference_logo, cropped_logo)

    return {
        "verified": orb_ok,
        "method": "ORB",
        "orb_score": orb_score
    }


# =========================
# TEST
# =========================
if __name__ == "__main__":
    reference_logo = "TextExtraction/known_logos/vesit.png"
    cropped_logo = "extracted_logo.png"

    result = verify_logo_hybrid(reference_logo, cropped_logo)
    print(result)
