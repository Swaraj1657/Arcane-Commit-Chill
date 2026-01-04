import pandas as pd
import re

# =========================
# CONFIG
# =========================
<<<<<<< Updated upstream
COLLEGE_DB_PATH = "College-ALL COLLEGE.xlsx"
=======
import os
COLLEGE_DB_PATH = os.path.join(os.path.dirname(__file__), "College-ALL COLLEGE.xlsx")

TRUSTED_PRIVATE_ISSUERS = [
    "mathworks",
    "coursera",
    "aws",
    "google",
    "microsoft",
    "nptel"
]
>>>>>>> Stashed changes

# =========================
# HELPERS
# =========================
def normalize(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text.strip()

# =========================
# CORE VERIFICATION LOGIC
# =========================
def verify_college_from_db(institute_name: str) -> dict:
    """
    Verifies institute name against trusted college database
    """

    if not institute_name:
        return {
            "verified": False,
            "status": "INSTITUTE_NAME_MISSING",
            "source": "College-ALL COLLEGE.xlsx"
        }

    df = pd.read_excel(COLLEGE_DB_PATH)

    normalized_target = normalize(institute_name)

    # normalize each row (no column assumptions)
    df["__normalized__"] = df.apply(
        lambda row: normalize(" ".join(row.astype(str))),
        axis=1
    )

    match = df[df["__normalized__"].str.contains(normalized_target, na=False)]

    if len(match) > 0:
        return {
            "verified": True,
            "status": "VERIFIED",
            "matched_rows": len(match),
            "source": "College-ALL COLLEGE.xlsx"
        }

    return {
        "verified": False,
        "status": "NOT_FOUND",
        "source": "College-ALL COLLEGE.xlsx"
    }

# =========================
# ATTACH VERIFICATION TO OCR OUTPUT
# =========================
def attach_verification(structured_ocr_json: dict) -> dict:
    institution = structured_ocr_json.get("institution_details", {})

    # ---- BOARD / SCHOOL CERTIFICATE ----
    # if institution.get("board_name"):
    #     structured_ocr_json["institution_details"]["verification"] = {
    #         "verified": True,
    #         "status": "BOARD_VERIFIED",
    #         "authority": institution["board_name"]
    #     }

    #     structured_ocr_json["fraud_checks"] = {
    #         "institution_existence": "CONFIRMED",
    #         "risk_level": "LOW"
    #     }

    #     structured_ocr_json["verified_profile"] = {
    #         "auto_verified": True,
    #         "shareable": True
    #     }

    #     structured_ocr_json["confidence_score"] = 0.92
    #     return structured_ocr_json

    # ---- COLLEGE / UNIVERSITY CERTIFICATE ----
    institute_name = (
        institution.get("institute_name")
        or institution.get("name")
        or institution.get("college_name")
    )

    verification_result = verify_college_from_db(institute_name)
    structured_ocr_json["institution_details"]["verification"] = verification_result

    structured_ocr_json["fraud_checks"] = {
        "institution_existence": verification_result["status"],
        "risk_level": "LOW" if verification_result["verified"] else "HIGH"
    }

<<<<<<< Updated upstream
    structured_ocr_json["verified_profile"] = {
        "auto_verified": verification_result["verified"],
        "shareable": True
=======
    data["fraud_checks"]["risk_level"] = (
        "LOW" if verification["verified"] else "HIGH"
    )

    data["verified_profile"]["auto_verified"] = verification["verified"]
    data["confidence_score"] = 0.95 if verification["verified"] else 0.45

    # =========================
    # 4️⃣ LOGO VERIFICATION (SUPPORTING)
    # =========================
    logo_result = {"verified": False, "error": "Logo verification not available"}
    try:
        logo_dir = os.path.join(os.path.dirname(__file__), "known_logos")
        reference_logo = os.path.join(logo_dir, "vesit.png")
        cropped_logo = os.path.join(os.path.dirname(__file__), "extracted_logo.png")
        
        if os.path.exists(reference_logo) and os.path.exists(cropped_logo):
            logo_result = verify_logo_hybrid(
                reference_logo=reference_logo,
                cropped_logo=cropped_logo
            )
    except Exception as e:
        logo_result = {"verified": False, "error": str(e)}

    data["institution_details"]["logo_verification"] = logo_result

    if not logo_result.get("verified", False) and "error" not in logo_result:
        # Only penalize if logo verification was attempted and failed
        # (not if it wasn't available)
        data["fraud_checks"]["risk_level"] = "HIGH"
        data["confidence_score"] -= 0.2

    # =========================
    # EXPLAINABILITY
    # =========================
    data["explainability"] = {
        "why_verified": [
            "Institute exists in approved registry",
            "Certificate issued by recognized authority"
        ],
        "why_risk": [] if data["fraud_checks"]["risk_level"] == "LOW" else [
            "Logo verification failed",
            "Institute not found in registry"
        ]
>>>>>>> Stashed changes
    }

    structured_ocr_json["confidence_score"] = (
        0.95 if verification_result["verified"] else 0.45
    )

    return structured_ocr_json



def add_verification_summary(data: dict) -> dict:
    verification = data.get("institution_details", {}).get("verification", {})

    data["verification_summary"] = {
        "institution_verified": verification.get("verified", False),
        "verification_status": verification.get("status"),
        "risk_level": data.get("fraud_checks", {}).get("risk_level"),
        "confidence_score": data.get("confidence_score"),
        "auto_verified": data.get("verified_profile", {}).get("auto_verified"),
        "source": verification.get("source", "UNKNOWN")
    }

    return data
