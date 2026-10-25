import logging

from flask import Blueprint, jsonify, request

from db import get_db_connection
from config import Config
from middleware.auth_middleware import token_required
from services.analysis_service import row_to_dict, save_analysis
from services.ai_explanation_service import explain_analysis
from services.ai_provider_errors import AIConfigurationError, AIProviderError
from services.threat_detection_service import analyze_message
from services.url_analysis_service import analyze_url

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")
log = logging.getLogger(__name__)


def analyze_and_save(kind, text, detector):
    try:
        result = detector(text)
        return jsonify({"status": "success", "analysis": save_analysis(request.user["user_id"], kind, text, result)})
    except ValueError as error:
        return jsonify({"status": "error", "message": str(error)}), 400
    except Exception:
        log.exception("Analysis request failed")
        return jsonify({"status": "error", "message": "Analysis could not be completed"}), 500


@analysis_bp.post("/message")
@token_required
def message():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "A JSON request body is required"}), 400
    value = data.get("message")
    if not isinstance(value, str) or not value.strip() or len(value) > 20000:
        return jsonify({"status": "error", "message": "Message must contain 1 to 20000 characters"}), 400
    return analyze_and_save("message", value.strip(), analyze_message)


@analysis_bp.post("/url")
@token_required
def url():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "A JSON request body is required"}), 400
    return analyze_and_save(
        "url", data.get("url"),
        lambda value: analyze_url(value, check_threat_intel=data.get("check_threat_intel") is True),
    )


@analysis_bp.get("/history")
@token_required
def history():
    try:
        page = max(1, int(request.args.get("page", "1")))
        per_page = min(100, max(1, int(request.args.get("per_page", "20"))))
    except ValueError:
        return jsonify({"status": "error", "message": "page and per_page must be integers"}), 400
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM analyses WHERE user_id = %s", (request.user["user_id"],))
            total = cursor.fetchone()[0]
            cursor.execute("""SELECT id, analysis_type, input_text, risk_score, threat_type, status, created_at,
                       detection_method, model_version FROM analyses WHERE user_id = %s
                       ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s""",
                           (request.user["user_id"], per_page, (page - 1) * per_page))
            items = [row_to_dict(r) for r in cursor.fetchall()]
        return jsonify({"status": "success", "items": items, "page": page, "per_page": per_page, "total": total})
    finally:
        connection.close()


@analysis_bp.get("/<int:analysis_id>")
@token_required
def detail(analysis_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT id, analysis_type, input_text, risk_score, threat_type, status, created_at,
                       detection_method, model_version FROM analyses WHERE id = %s AND user_id = %s""",
                           (analysis_id, request.user["user_id"]))
            row = cursor.fetchone()
            if not row:
                return jsonify({"status": "error", "message": "Analysis not found"}), 404
            result = row_to_dict(row)
            cursor.execute("SELECT indicator, severity, evidence FROM analysis_indicators WHERE analysis_id = %s ORDER BY id", (analysis_id,))
            result["indicators"] = [{"indicator": r[0], "severity": r[1], "evidence": r[2]} for r in cursor.fetchall()]
            cursor.execute("SELECT recommendation FROM recommendations WHERE analysis_id = %s ORDER BY id", (analysis_id,))
            result["recommendations"] = [r[0] for r in cursor.fetchall()]
        return jsonify({"status": "success", "analysis": result})
    finally:
        connection.close()


@analysis_bp.post("/<int:analysis_id>/explanation")
@token_required
def explanation(analysis_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.get("share_with_gemini") is not True:
        return jsonify({"status": "error", "message": "Explicit consent is required before sending this analysis to Gemini"}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT analysis_type, input_text, risk_score, threat_type
                           FROM analyses WHERE id = %s AND user_id = %s""",
                           (analysis_id, request.user["user_id"]))
            row = cursor.fetchone()
            if not row:
                return jsonify({"status": "error", "message": "Analysis not found"}), 404
            analysis_type, input_text, risk_score, threat_type = row
            cursor.execute("SELECT indicator, severity, evidence FROM analysis_indicators WHERE analysis_id = %s ORDER BY id", (analysis_id,))
            indicators = [{"indicator": item[0], "severity": item[1], "evidence": item[2]} for item in cursor.fetchall()]
            cursor.execute("SELECT recommendation FROM recommendations WHERE analysis_id = %s ORDER BY id", (analysis_id,))
            recommendations = [item[0] for item in cursor.fetchall()]
    finally:
        connection.close()

    try:
        text = explain_analysis(analysis_type, input_text, risk_score, threat_type, indicators, recommendations)
        return jsonify({"status": "success", "explanation": text, "provider": "Gemini", "model": Config.GEMINI_MODEL})
    except AIConfigurationError as error:
        return jsonify({"status": "error", "message": str(error)}), 503
    except AIProviderError as error:
        return jsonify({"status": "error", "message": str(error)}), 502
