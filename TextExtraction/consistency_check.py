from rapidfuzz import fuzz

def consistency_check(certificates: list) -> dict:
    names = []
    fathers = []

    for c in certificates:
        s = c.get("student_details", {})
        if s.get("name"):
            names.append(s["name"])
        if s.get("father_name"):
            fathers.append(s["father_name"])

    name_score = min(
        fuzz.ratio(names[0], n) for n in names[1:]
    ) if len(names) > 1 else 100

    father_score = min(
        fuzz.ratio(fathers[0], f) for f in fathers[1:]
    ) if len(fathers) > 1 else 100

    risk = "LOW"
    if name_score < 85 or father_score < 80:
        risk = "HIGH"

    return {
        "name_consistency": name_score,
        "father_name_consistency": father_score,
        "risk_level": risk
    }
