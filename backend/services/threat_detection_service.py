import re

from services.ml_classifier import classify_spam_like

RULES = [
    ("urgency", "medium", 12, re.compile(r"\b(urgent|immediately|act now|within 24 hours|last warning|today)\b", re.I)),
    ("account_threat", "high", 20, re.compile(r"\b(account (?:will be )?(?:blocked|suspended|closed|deactivated)|account closure)\b", re.I)),
    ("credential_request", "high", 28, re.compile(r"\b(?:share|send|provide|enter|confirm|verify|give)\b.{0,35}\b(?:otp|password|pin|cvv|card number|bank details|login details)\b|\b(?:otp|password|pin|cvv)\b.{0,35}\b(?:share|send|provide|enter|confirm)\b", re.I)),
    ("link_present", "medium", 14, re.compile(r"https?://[^\s<>]+|\bwww\.[^\s<>]+", re.I)),
    ("verification_request", "medium", 14, re.compile(r"\b(verify (?:your )?(?:account|identity|kyc)|kyc update|complete verification)\b", re.I)),
    ("payment_request", "high", 22, re.compile(r"\b(send|transfer|pay|wire)\b.{0,40}\b(money|payment|funds|gift card|crypto)\b", re.I)),
    ("authority_claim", "medium", 10, re.compile(r"\b(bank|government|police|tax department|support team|security team)\b", re.I)),
]


def analyze_message(message):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message must not be empty")
    indicators, score = [], 0
    matched = set()
    for key, severity, points, pattern in RULES:
        match = pattern.search(message)
        if not match:
            continue
        # Urgency and verification are related pressure signals: count the stronger one.
        group = "pressure" if key in {"urgency", "verification_request"} else key
        if group in matched:
            continue
        matched.add(group)
        score += points
        indicators.append({"indicator": key, "severity": severity,
                           "evidence": f"Matched wording: “{match.group(0)[:100]}”"})
    score = min(score, 100)
    ml_result = classify_spam_like(message)
    if ml_result and ml_result["is_spam_like"]:
        indicators.append({
            "indicator": "ml_spam_like_signal",
            "severity": "low",
            "evidence": "The local text classifier found a spam-like pattern. It was trained on general SMS data; this alone does not indicate phishing or prove fraud.",
        })
        score = min(100, score + 10)
    level = "CRITICAL" if score >= 85 else "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW"
    if not matched and ml_result and ml_result["is_spam_like"]:
        threat_type = "Potential unsolicited spam-like message"
    elif not indicators:
        threat_type = "No major threat indicators detected"
    elif "credential_request" in matched or "payment_request" in matched:
        threat_type = "Potential phishing or social engineering"
    else:
        threat_type = "Suspicious message"
    recommendations = ["Do not click unexpected links or reply with sensitive information.",
                       "Verify the request through the organization’s official app, website, or independently verified phone number."] if indicators else ["No major indicators were found by these rules. Verify unexpected requests through an official channel."]
    if "credential_request" in matched:
        recommendations.insert(0, "Never share an OTP, password, PIN, or CVV; legitimate support staff should not ask for them.")
    if "payment_request" in matched:
        recommendations.append("If you already sent money, contact your bank promptly using an independently verified number and consult your official cybercrime reporting channel.")
    return {"risk_score": score, "risk_level": level, "threat_type": threat_type,
            "indicators": indicators, "recommendations": recommendations,
            "detection_method": "rules+local_ml" if ml_result else "explainable_rules",
            "model_version": ml_result["model_version"] if ml_result else "rules-v2"}
