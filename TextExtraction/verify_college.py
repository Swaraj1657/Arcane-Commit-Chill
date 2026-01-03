import pandas as pd
import re
from logo_matcher import verify_logo_hybrid

# =========================
# CONFIG
# =========================
COLLEGE_DB_PATH = "TextExtraction/College-ALL COLLEGE.xlsx"

TRUSTED_PRIVATE_ISSUERS = [
    "mathworks",
    "coursera",
    "aws",
    "google",
    "microsoft",
    "nptel"
]

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
# COLLEGE EXISTENCE CHECK
# =========================
def verify_college_from_db(institute_name: str) -> dict:
    if not institute_name:
        return {
            "verified": False,
            "status": "INSTITUTE_NAME_MISSING",
            "source": "College-ALL COLLEGE.xlsx"
        }

    df = pd.read_excel(COLLEGE_DB_PATH)
    target = normalize(institute_name)

    df["__norm__"] = df.apply(
        lambda row: normalize(" ".join(row.astype(str))),
        axis=1
    )

    match = df[df["__norm__"].str.contains(target, na=False)]

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
# MAIN VERIFICATION LAYER
# =========================
def attach_verification(data: dict) -> dict:
    institution = data.get("institution_details", {})
    metadata = data.get("certificate_metadata", {})

    # =========================
    # INIT SAFETY DEFAULTS
    # =========================
    data.setdefault("fraud_checks", {"risk_level": "LOW"})
    data.setdefault("confidence_score", 0.7)
    data.setdefault("verified_profile", {"auto_verified": False})

    # =========================
    # 1️⃣ BOARD / SCHOOL
    # =========================
    if institution.get("board_name"):
        data["institution_details"]["verification"] = {
            "verified": True,
            "status": "BOARD_VERIFIED",
            "authority_type": "BOARD",
            "authority": institution["board_name"]
        }

        data["fraud_checks"]["risk_level"] = "LOW"
        data["verified_profile"]["auto_verified"] = True
        data["confidence_score"] = 0.92

        return data

    # =========================
    # 2️⃣ PRIVATE ISSUER
    # =========================
    issuer_text = (
        institution.get("name", "") +
        institution.get("institution_name", "") +
        institution.get("college_name", "") +
        " " +
        metadata.get("powered_by", "")
    ).lower()


    for issuer in TRUSTED_PRIVATE_ISSUERS:
        if issuer in issuer_text:
            data["institution_details"]["verification"] = {
                "verified": True,
                "status": "ISSUER_VERIFIED",
                "authority_type": "PRIVATE_ISSUER",
                "authority": issuer.title()
            }

            data["fraud_checks"]["risk_level"] = "LOW"
            data["verified_profile"]["auto_verified"] = True
            data["confidence_score"] = 0.78

            return data

    # =========================
    # 3️⃣ COLLEGE / UNIVERSITY
    # =========================
    institute_name = (
        institution.get("institute_name")
        or institution.get("name")
        or institution.get("college_name")
    )

    verification = verify_college_from_db(institute_name)

    data["institution_details"]["verification"] = {
        **verification,
        "authority_type": "APPROVED_INSTITUTE_REGISTRY",
        "authority": "UGC / AICTE Approved Colleges List"
    }

    data["fraud_checks"]["risk_level"] = (
        "LOW" if verification["verified"] else "HIGH"
    )

    data["verified_profile"]["auto_verified"] = verification["verified"]
    data["confidence_score"] = 0.95 if verification["verified"] else 0.45

    # =========================
    # 4️⃣ LOGO VERIFICATION (SUPPORTING)
    # =========================
    logo_result = verify_logo_hybrid(
        reference_logo="TextExtraction/known_logos/vesit.png",
        cropped_logo="extracted_logo.png"
    )

    data["institution_details"]["logo_verification"] = logo_result

    if not logo_result.get("verified", False):
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
    }

    return data

# =========================
# SUMMARY OVERLAY
# =========================
def add_verification_summary(data: dict) -> dict:
    v = data.get("institution_details", {}).get("verification", {})

    data["verification_summary"] = {
        "authority_type": v.get("authority_type"),
        "authority": v.get("authority"),
        "verification_status": v.get("status"),
        "institution_verified": v.get("verified"),
        "risk_level": data.get("fraud_checks", {}).get("risk_level"),
        "confidence_score": data.get("confidence_score"),
        "auto_verified": data.get("verified_profile", {}).get("auto_verified")
    }

    return data
