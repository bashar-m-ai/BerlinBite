"""Transparent time-based heuristic; never a live occupancy measurement or ML model."""
from datetime import datetime
from zoneinfo import ZoneInfo

def crowd_estimate(visit: datetime) -> dict:
    local = visit.astimezone(ZoneInfo("Europe/Berlin"))
    score = 25
    reasons = []
    if 18 <= local.hour < 21:
        score += 35
        reasons.append("Typical dinner hours")
    elif 12 <= local.hour < 14:
        score += 20
        reasons.append("Typical lunch hours")
    if local.weekday() in (4, 5):
        score += 20
        reasons.append("Friday or Saturday")
    return {"label": "Busy" if score >= 65 else "Moderate" if score >= 40 else "Quiet",
            "score": score, "basis": reasons or ["Outside typical peak hours"],
            "disclaimer": "Unvalidated time-based estimate, not live occupancy. Individual restaurants may differ."}
