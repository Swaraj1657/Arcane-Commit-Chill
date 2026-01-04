"""
Utility to map text.py processing results to Supabase certificates schema
"""
from datetime import datetime
from typing import Dict, Any, List

def map_processing_result_to_schema(processing_result: Dict[str, Any], document_type: str = "DEGREE") -> Dict[str, Any]:
    """
    Maps the output from process_certificates to the Supabase certificates table schema.
    
    Args:
        processing_result: The result from process_certificates (contains certificates list)
        document_type: Document type (MARKSHEET, DEGREE, INTERNSHIP, COURSE, OTHER)
    
    Returns:
        Dictionary matching the certificates table schema
    """
    # Get the first certificate (since we process one at a time via API)
    if not processing_result.get("certificates") or len(processing_result["certificates"]) == 0:
        raise ValueError("No certificates found in processing result")
    
    cert_data = processing_result["certificates"][0]
    verification_summary = cert_data.get("verification_summary", {})
    student_details = cert_data.get("student_details", {})
    academic_details = cert_data.get("academic_details", {})
    institution_details = cert_data.get("institution_details", {})
    certificate_metadata = cert_data.get("certificate_metadata", {})
    fraud_checks = cert_data.get("fraud_checks", {})
    
    # Determine verification status
    risk_level = verification_summary.get("risk_level", "HIGH")
    confidence_score = verification_summary.get("confidence_score", 0.0)
    auto_verified = verification_summary.get("auto_verified", False)
    
    if auto_verified and risk_level == "LOW":
        verification_status = "VERIFIED"
    elif confidence_score > 0.7:
        verification_status = "PARTIALLY_VERIFIED"
    elif risk_level == "HIGH":
        verification_status = "FAILED"
    else:
        verification_status = "PENDING"
    
    # Determine verification source
    verification_source = "OCR"
    if cert_data.get("verification_summary", {}).get("digilocker_verified"):
        verification_source = "DigiLocker"
    elif institution_details.get("verification", {}).get("authority_type") == "BOARD":
        verification_source = "NAD"
    
    # Extract issued date
    issued_date = None
    if certificate_metadata.get("issue_date"):
        try:
            issued_date = datetime.strptime(certificate_metadata["issue_date"], "%Y-%m-%d").date().isoformat()
        except:
            pass
    
    # Map to schema
    mapped_data = {
        "document_type": document_type,
        "extracted_student_name": student_details.get("name"),
        "extracted_roll_number": student_details.get("roll_number") or academic_details.get("roll_number"),
        "extracted_registration_number": student_details.get("registration_number"),
        "extracted_apaar_id": student_details.get("apaar_id"),
        "extracted_father_name": student_details.get("father_name"),
        "extracted_mother_name": student_details.get("mother_name"),
        "extracted_degree": academic_details.get("degree") or academic_details.get("degree_name"),
        "extracted_branch": academic_details.get("branch") or academic_details.get("field_of_study"),
        "extracted_semester": academic_details.get("semester"),
        "extracted_examination": academic_details.get("examination"),
        "issued_date": issued_date,
        "extracted_institution_name": (
            institution_details.get("institute_name") or 
            institution_details.get("name") or 
            institution_details.get("college_name") or
            institution_details.get("university_name")
        ),
        "extracted_established_year": institution_details.get("established_year"),
        "extracted_organization_type": _determine_organization_type(institution_details),
        "verification_source": verification_source,
        "verification_status": verification_status,
        "forgery_risk_score": int(confidence_score * 100) if confidence_score else None,
        "verdict": _determine_verdict(risk_level, confidence_score, auto_verified),
        "extracted_visuals": cert_data.get("institution_details", {}).get("logo_verification", {}),
        "raw_extracted_data": cert_data,
    }
    
    return mapped_data

def _determine_organization_type(institution_details: Dict[str, Any]) -> str:
    """Determine organization type from institution details"""
    if institution_details.get("board_name"):
        return "BOARD"
    elif institution_details.get("university_name") or "university" in str(institution_details.get("name", "")).lower():
        return "UNIVERSITY"
    elif institution_details.get("college_name") or "college" in str(institution_details.get("name", "")).lower():
        return "COLLEGE"
    elif institution_details.get("company_name") or "company" in str(institution_details.get("name", "")).lower():
        return "COMPANY"
    else:
        return "UNKNOWN"

def _determine_verdict(risk_level: str, confidence_score: float, auto_verified: bool) -> str:
    """Determine verdict based on risk level and verification status"""
    if risk_level == "LOW" and auto_verified:
        return "LEGITIMATE"
    elif risk_level == "HIGH":
        return "SUSPICIOUS"
    elif confidence_score > 0.7:
        return "LIKELY_LEGITIMATE"
    else:
        return "REQUIRES_REVIEW"

