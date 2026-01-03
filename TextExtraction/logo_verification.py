import os
import requests
import wikipediaapi
import tldextract
from bs4 import BeautifulSoup
from rapidfuzz import fuzz
from urllib.parse import urljoin, urlparse

import torch
import open_clip
from PIL import Image

# ================= USER INPUT =================
INSTITUTE_NAME = "Vivekanand Education Society's Institute of Technology"
OCR_DEGREE_TEXT = "Bachelor of Engineering"
EXTRACTED_LOGO_PATH = "logos_opensource/degree_p1_6_colored_region_color_50.png"   # 🔴 user-provided logo
# ==============================================

# ================= CONFIG ======================
OUTPUT_DIR = "verification_output"
REFERENCE_DIR = "reference_logos"
ALLOWED_DOMAINS = [".ac.in", ".edu.in", ".gov.in"]
USER_AGENT = "IEEE-ARCANE-AcademicVerifier/1.0 (contact: swaraj@gmail.com)"
TEXT_MATCH_THRESHOLD = 75
LOGO_SIM_THRESHOLD = 0.70
# ==============================================

HEADERS = {"User-Agent": USER_AGENT}


# -------------------- UTILS --------------------

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(REFERENCE_DIR, exist_ok=True)


def get_wiki():
    return wikipediaapi.Wikipedia(
        user_agent=USER_AGENT,
        language="en"
    )


def scrape_text(url):
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        for t in soup(["script", "style", "noscript"]):
            t.decompose()
        return " ".join(soup.stripped_strings).lower()
    except:
        return ""


def fuzzy_match(label, expected, actual_text):
    score = fuzz.partial_ratio(expected.lower(), actual_text)
    return {
        "field": label,
        "score": score,
        "matched": score >= TEXT_MATCH_THRESHOLD
    }


# -------------------- LOGO (AI) --------------------

def load_clip():
    model, preprocess, _ = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    model.eval()
    return model, preprocess


def clip_similarity(img1, img2):
    model, preprocess = load_clip()

    def encode(path):
        image = preprocess(Image.open(path).convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            emb = model.encode_image(image)
            emb /= emb.norm(dim=-1, keepdim=True)
        return emb

    return (encode(img1) @ encode(img2).T).item()


# -------------------- WIKIPEDIA --------------------

def fetch_wikipedia_logo():
    wiki = get_wiki()
    page = wiki.page(INSTITUTE_NAME)

    if not page.exists():
        return None, None

    html = requests.get(page.fullurl, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    infobox = soup.find("table", class_="infobox")
    if not infobox:
        return page.fullurl, None

    img = infobox.find("img")
    if not img:
        return page.fullurl, None

    logo_url = "https:" + img["src"]
    path = os.path.join(REFERENCE_DIR, "wiki_logo.png")

    with open(path, "wb") as f:
        f.write(requests.get(logo_url, headers=HEADERS).content)

    return page.fullurl, path


def find_official_site():
    wiki = get_wiki()
    page = wiki.page(INSTITUTE_NAME)

    if not page.exists():
        return None

    html = requests.get(page.fullurl, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("http"):
            continue

        ext = tldextract.extract(href)
        if f".{ext.suffix}" in ALLOWED_DOMAINS:
            return href

    return None


def fetch_site_logo(site_url):
    try:
        html = requests.get(site_url, headers=HEADERS).text
        soup = BeautifulSoup(html, "html.parser")
    except:
        return None

    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue

        full = urljoin(site_url, src)
        name = os.path.basename(urlparse(full).path).lower()

        if any(k in name for k in ["logo", "emblem", "seal"]):
            path = os.path.join(REFERENCE_DIR, "official_logo.png")
            with open(path, "wb") as f:
                f.write(requests.get(full, headers=HEADERS).content)
            return path

    return None


# -------------------- VERIFICATION --------------------

def verify():
    report = []
    score = 0

    # Wikipedia text
    wiki_url, wiki_logo = fetch_wikipedia_logo()
    if wiki_url:
        wiki_text = scrape_text(wiki_url)
        r = fuzzy_match("Institute Name (Wikipedia)", INSTITUTE_NAME, wiki_text)
        report.append(r)
        if r["matched"]:
            score += 25

    # Official site text
    site = find_official_site()
    if site:
        site_text = scrape_text(site)

        r1 = fuzzy_match("Institute Name (Official Site)", INSTITUTE_NAME, site_text)
        report.append(r1)
        if r1["matched"]:
            score += 25

        r2 = fuzzy_match("Degree / Course", OCR_DEGREE_TEXT, site_text)
        report.append(r2)
        if r2["matched"]:
            score += 20

        official_logo = fetch_site_logo(site)

        # Logo verification
        if wiki_logo and official_logo:
            sim = clip_similarity(EXTRACTED_LOGO_PATH, wiki_logo)
            sim_score = int(sim * 100)

            report.append({
                "field": "Logo Similarity (User vs Wikipedia)",
                "score": sim_score,
                "matched": sim >= LOGO_SIM_THRESHOLD
            })

            if sim >= LOGO_SIM_THRESHOLD:
                score += 15
            elif sim >= 0.55:
                score += 7

    return score, report


# -------------------- MAIN --------------------

if __name__ == "__main__":
    ensure_dirs()

    final_score, verification_report = verify()

    print("\n========== ACADEMIC LEGITIMACY REPORT ==========")
    print(f"🏫 Institute : {INSTITUTE_NAME}")
    print(f"🎓 Degree   : {OCR_DEGREE_TEXT}")
    print("------------------------------------------------")

    for r in verification_report:
        status = "✅ MATCH" if r["matched"] else "❌ MISMATCH"
        print(f"{status} | {r['field']} | Score: {r['score']}")

    print("------------------------------------------------")
    print(f"⭐ FINAL CONFIDENCE SCORE: {final_score}/85")

    if final_score >= 65:
        print("✅ VERDICT: LIKELY LEGIT (Strong web & logo consistency)")
    elif final_score >= 45:
        print("⚠️ VERDICT: PARTIALLY VERIFIED (Needs manual review)")
    else:
        print("❌ VERDICT: LOW CONFIDENCE (Suspicious)")
