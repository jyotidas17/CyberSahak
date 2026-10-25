"""Authenticated, consent-gated CyberSahak chat endpoint."""
from flask import Blueprint, jsonify, request

from middleware.auth_middleware import token_required
from services.ai_provider_errors import AIConfigurationError, AIProviderError
from services.assistant_service import generate_reply

assistant_bp = Blueprint("assistant", __name__, url_prefix="/api/assistant")


@assistant_bp.post("/chat")
@token_required
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.get("consent_to_gemini") is not True:
        return jsonify({"status": "error", "message": "Consent is required before sending chat messages to Gemini"}), 400

    messages = data.get("messages")
    if not isinstance(messages, list) or not messages or len(messages) > 21:
        return jsonify({"status": "error", "message": "Send between 1 and 21 recent chat messages"}), 400

    safe_messages = []
    total_chars = 0
    expected_role = "user"
    for item in messages:
        if not isinstance(item, dict) or item.get("role") != expected_role:
            return jsonify({"status": "error", "message": "Chat messages must alternate between user and assistant"}), 400
        content = item.get("content")
        if not isinstance(content, str) or not content.strip() or len(content) > 3000:
            return jsonify({"status": "error", "message": "Each chat message must contain 1 to 3000 characters"}), 400
        total_chars += len(content)
        safe_messages.append({"role": expected_role, "content": content.strip()})
        expected_role = "assistant" if expected_role == "user" else "user"
    if safe_messages[-1]["role"] != "user" or total_chars > 16000:
        return jsonify({"status": "error", "message": "A user message is required and recent chat text must stay under 16000 characters"}), 400

    try:
        reply = generate_reply(safe_messages)
        return jsonify({"status": "success", "reply": reply, "provider": "Gemini"})
    except AIConfigurationError as error:
        return jsonify({"status": "error", "message": str(error)}), 503
    except AIProviderError as error:
        return jsonify({"status": "error", "message": str(error)}), 502
