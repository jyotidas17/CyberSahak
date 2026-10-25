import ipaddress
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from config import Config


def _query_urlhaus(url):
    """Query URLhaus only after the user explicitly opts in."""
    if not Config.URLHAUS_AUTH_KEY:
        return {"status": "not_configured"}
    request = Request(
        "https://urlhaus-api.abuse.ch/v1/url/",
        data=urlencode({"url": url}).encode("utf-8"),
        headers={"Auth-Key": Config.URLHAUS_AUTH_KEY,
                 "Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": "CyberSahak/1.0"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=6) as response:
            payload = json.loads(response.read(256 * 1024).decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return {"status": "unavailable"}
    if payload.get("query_status") == "ok":
        return {
            "status": "match",
            "source": "URLhaus",
            "reference": payload.get("urlhaus_reference"),
            "url_status": payload.get("url_status"),
            "threat": payload.get("threat"),
            "date_added": payload.get("date_added"),
            "tags": payload.get("tags", [])[:10],
        }
    if payload.get("query_status") == "no_results":
        return {"status": "no_match", "source": "URLhaus"}
    return {"status": "unavailable"}


def analyze_url(value, check_threat_intel=False):
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise ValueError("A URL between 1 and 2048 characters is required")
    raw = value.strip()
    candidate = raw if "://" in raw else "https://" + raw
    try:
        parsed = urlsplit(candidate)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError("URL format is invalid") from error
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise ValueError("Only HTTP and HTTPS URLs with a hostname are supported")
    indicators, score = [], 0
    def add(key, severity, points, evidence):
        nonlocal score
        score += points
        indicators.append({"indicator": key, "severity": severity, "evidence": evidence})
    if parsed.scheme != "https":
        add("unencrypted_scheme", "medium", 12, "The link uses HTTP rather than HTTPS.")
    try:
        ipaddress.ip_address(hostname)
        add("ip_address_host", "high", 25, "The hostname is an IP address rather than a named domain.")
    except ValueError:
        pass
    try:
        hostname.encode("ascii")
        non_ascii = False
    except UnicodeEncodeError:
        non_ascii = True
    if non_ascii or hostname.lower().startswith("xn--") or ".xn--" in hostname.lower():
        add("internationalized_domain", "medium", 20, "The hostname contains Unicode or IDN punycode; inspect it carefully for lookalikes.")
    if len(hostname.split(".")) > 4:
        add("deep_subdomains", "medium", 12, "The hostname has more than four labels, which can obscure its registered domain.")
    labels = hostname.lower().split(".")
    known_brands = {"paypal", "google", "microsoft", "apple", "amazon", "facebook", "instagram", "netflix", "bank"}
    if len(labels) > 2 and any(any(brand in label for brand in known_brands) for label in labels[:-2]):
        add("brand_like_subdomain", "medium", 20, "A familiar service or banking term appears in a subdomain rather than the apparent registered domain.")
    if port and port not in {80, 443}:
        add("unusual_port", "medium", 14, f"The URL specifies the unusual port {port}.")
    if parsed.username or parsed.password or "@" in parsed.netloc.rsplit(":", 1)[0]:
        add("userinfo_or_at_sign", "high", 20, "The authority section includes user information or an @ sign that can mislead readers.")
    if re.search(r"%[0-9a-fA-F]{2}", parsed.path + parsed.query):
        add("encoded_url_content", "low", 8, "The URL contains percent-encoded characters.")
    if re.search(r"(login|verify|secure|account|update|wallet|banking)", parsed.path, re.I):
        add("sensitive_path_terms", "low", 8, "The path contains terms often used in sign-in or account prompts; this alone does not establish risk.")
    if not check_threat_intel:
        threat_intelligence = {"status": "not_checked"}
    elif parsed.username or parsed.password:
        # Never transmit a URL that embeds credentials to a third party.
        threat_intelligence = {"status": "not_checked_sensitive_url"}
    else:
        threat_intelligence = _query_urlhaus(candidate)
    if threat_intelligence["status"] == "match":
        add("urlhaus_known_malware_url", "high", 65,
            "URLhaus lists this URL as a malware-distribution URL. "
            f"Record status: {threat_intelligence.get('url_status', 'unknown')}; "
            f"reported: {threat_intelligence.get('date_added', 'date unavailable')}. "
            f"URLhaus record: {threat_intelligence.get('reference', 'link unavailable')}.")
    elif threat_intelligence["status"] == "no_match":
        indicators.append({"indicator": "urlhaus_no_match", "severity": "low",
                           "evidence": "No matching record was returned by URLhaus. This does not prove that the URL is safe.",
                           "source": "URLhaus"})
    elif threat_intelligence["status"] == "unavailable":
        indicators.append({"indicator": "threat_intelligence_unavailable", "severity": "low",
                           "evidence": "URLhaus could not be reached or did not return a usable result. No feed verdict was made."})
    elif threat_intelligence["status"] == "not_configured":
        indicators.append({"indicator": "threat_intelligence_not_configured", "severity": "low",
                           "evidence": "URLhaus lookup was requested, but the backend has no URLHAUS_AUTH_KEY configured."})
    elif threat_intelligence["status"] == "not_checked_sensitive_url":
        indicators.append({"indicator": "threat_intelligence_not_checked", "severity": "low",
                           "evidence": "The URL contains embedded credentials, so it was not sent to URLhaus."})
    else:
        indicators.append({"indicator": "threat_intelligence_not_checked", "severity": "low",
                           "evidence": "URLhaus lookup was not requested. The URL was checked only with local URL signals."})
    score = min(score, 100)
    level = "CRITICAL" if score >= 85 else "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW"
    if threat_intelligence["status"] == "match":
        threat_type = "Known malware-distribution URL reported by URLhaus"
    elif score:
        threat_type = "Potentially suspicious URL"
    else:
        threat_type = "No warning signals found; safety not confirmed"
    recommendations = ["Do not open this link. URLhaus reports it as a malware-distribution URL.",
                       "If you already downloaded a file from it, do not open the file; run a security scan and seek trusted technical help."] if threat_intelligence["status"] == "match" else ["Do not open a link you did not expect. Check the domain carefully and visit the organization by typing its known address."]
    if threat_intelligence["status"] == "no_match":
        recommendations.append("URLhaus found no matching record. This is not proof that the URL is safe; new or unreported threats may be missing.")
    elif threat_intelligence["status"] in {"unavailable", "not_configured", "not_checked", "not_checked_sensitive_url"}:
        recommendations.append("Threat-feed lookup did not provide a verdict. Heuristic checks cannot guarantee that a link is safe.")
    return {"risk_score": score, "risk_level": level,
            "threat_type": threat_type,
            "indicators": indicators,
            "recommendations": recommendations,
            "threat_intelligence": threat_intelligence,
            "detection_method": "url_heuristics+urlhaus" if threat_intelligence["status"] in {"match", "no_match"} else "url_heuristics",
            "model_version": "url-rules-v2"}
