from flask import Blueprint, jsonify, request
from datetime import timezone

from db import get_db_connection
from middleware.auth_middleware import token_required
from services.analysis_service import row_to_dict

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.get("/summary")
@token_required
def summary():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT COUNT(*),
                COUNT(*) FILTER (WHERE risk_score >= 60),
                COUNT(*) FILTER (WHERE risk_score >= 30 AND risk_score < 60),
                COUNT(*) FILTER (WHERE risk_score < 30)
                FROM analyses WHERE user_id = %s""", (request.user["user_id"],))
            total, high, medium, low = cursor.fetchone()
            cursor.execute("SELECT analysis_type, COUNT(*) FROM analyses WHERE user_id = %s GROUP BY analysis_type", (request.user["user_id"],))
            types = {key: count for key, count in cursor.fetchall()}
        return jsonify({"status": "success", "total": total, "risk_counts": {"HIGH": high, "MEDIUM": medium, "LOW": low}, "analysis_types": types})
    finally:
        connection.close()


@dashboard_bp.get("/recent")
@token_required
def recent():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT id, analysis_type, input_text, risk_score, threat_type, status, created_at,
                detection_method, model_version FROM analyses WHERE user_id = %s
                ORDER BY created_at DESC, id DESC LIMIT 10""", (request.user["user_id"],))
            items = [row_to_dict(row) for row in cursor.fetchall()]
        return jsonify({"status": "success", "items": items})
    finally:
        connection.close()


@dashboard_bp.get("/threat-intelligence")
@token_required
def threat_intelligence():
    """Return only this signed-in user's saved URL and URLhaus results."""
    user_id = request.user["user_id"]
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""WITH url_checks AS (
                SELECT a.id, a.created_at, a.risk_score, a.threat_type,
                    COALESCE(MAX(i.indicator) FILTER (WHERE i.indicator IN (
                        'urlhaus_known_malware_url', 'urlhaus_no_match',
                        'threat_intelligence_unavailable', 'threat_intelligence_not_configured',
                        'threat_intelligence_not_checked'
                    )), 'threat_intelligence_not_checked') AS intel_status
                FROM analyses a
                LEFT JOIN analysis_indicators i ON i.analysis_id = a.id
                WHERE a.user_id = %s AND a.analysis_type = 'url'
                GROUP BY a.id
            )
            SELECT COUNT(*),
                COUNT(*) FILTER (WHERE intel_status = 'urlhaus_known_malware_url'),
                COUNT(*) FILTER (WHERE intel_status = 'urlhaus_no_match'),
                COUNT(*) FILTER (WHERE intel_status IN (
                    'threat_intelligence_unavailable', 'threat_intelligence_not_configured'
                )),
                COUNT(*) FILTER (WHERE intel_status = 'threat_intelligence_not_checked')
            FROM url_checks""", (user_id,))
            total, matches, no_match, unavailable, not_checked = cursor.fetchone()

            cursor.execute("""WITH url_checks AS (
                SELECT a.id, a.created_at, a.risk_score, a.threat_type,
                    COALESCE(MAX(i.indicator) FILTER (WHERE i.indicator IN (
                        'urlhaus_known_malware_url', 'urlhaus_no_match',
                        'threat_intelligence_unavailable', 'threat_intelligence_not_configured',
                        'threat_intelligence_not_checked'
                    )), 'threat_intelligence_not_checked') AS intel_status
                FROM analyses a
                LEFT JOIN analysis_indicators i ON i.analysis_id = a.id
                WHERE a.user_id = %s AND a.analysis_type = 'url'
                GROUP BY a.id
            )
            SELECT id, created_at, risk_score, threat_type, intel_status
            FROM url_checks ORDER BY created_at DESC, id DESC LIMIT 10""", (user_id,))
            recent_checks = [{
                "analysis_id": row[0],
                "created_at": row[1].replace(tzinfo=timezone.utc).isoformat(),
                "risk_score": float(row[2]),
                "threat_type": row[3],
                "intel_status": row[4],
            } for row in cursor.fetchall()]
        return jsonify({
            "status": "success",
            "source": "URLhaus",
            "summary": {
                "urls_reviewed": total,
                "known_threat_matches": matches,
                "no_feed_match": no_match,
                "lookup_unavailable": unavailable,
                "not_checked": not_checked,
                "completed_lookups": matches + no_match,
            },
            "recent_checks": recent_checks,
        })
    finally:
        connection.close()
