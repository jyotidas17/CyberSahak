import logging
from datetime import timezone

from db import get_db_connection

log = logging.getLogger(__name__)


def save_analysis(user_id, analysis_type, input_text, result):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO analyses
                (user_id, analysis_type, input_text, risk_score, threat_type, confidence, status, detection_method, model_version)
                VALUES (%s, %s, %s, %s, %s, NULL, 'completed', %s, %s) RETURNING id, created_at""",
                (user_id, analysis_type, input_text, result["risk_score"], result["threat_type"], result["detection_method"], result["model_version"]))
            analysis_id, created_at = cursor.fetchone()
            for item in result["indicators"]:
                cursor.execute("INSERT INTO analysis_indicators (analysis_id, indicator, severity, evidence) VALUES (%s, %s, %s, %s)",
                               (analysis_id, item["indicator"], item["severity"], item.get("evidence", "")))
            for recommendation in result["recommendations"]:
                cursor.execute("INSERT INTO recommendations (analysis_id, recommendation, priority) VALUES (%s, %s, %s)",
                               (analysis_id, recommendation, "high" if result["risk_score"] >= 60 else "normal"))
        connection.commit()
        return {**result, "analysis_id": analysis_id, "analysis_type": analysis_type,
                "created_at": created_at.replace(tzinfo=timezone.utc).isoformat()}
    except Exception:
        connection.rollback()
        log.exception("Analysis persistence failed")
        raise
    finally:
        connection.close()


def row_to_dict(row):
    return {"analysis_id": row[0], "analysis_type": row[1], "input_text": row[2],
            "risk_score": float(row[3]), "threat_type": row[4], "status": row[5],
            "created_at": row[6].replace(tzinfo=timezone.utc).isoformat(),
            "detection_method": row[7], "model_version": row[8]}
