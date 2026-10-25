import jwt
from functools import wraps
from flask import request, jsonify
from config import Config


def token_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({
                "status": "error",
                "message": "Authorization token is required"
            }), 401

        try:

            # Expected format:
            # Bearer <token>

            parts = auth_header.split(" ")

            if len(parts) != 2 or parts[0].lower() != "bearer":
                return jsonify({
                    "status": "error",
                    "message": "Invalid authorization format"
                }), 401

            token = parts[1]

            if not Config.JWT_SECRET:
                return jsonify({"status": "error", "message": "Authentication is not configured"}), 503
            decoded_token = jwt.decode(
                token,
                Config.JWT_SECRET,
                algorithms=["HS256"]
            )

            # Store decoded user information
            request.user = decoded_token

        except jwt.ExpiredSignatureError:

            return jsonify({
                "status": "error",
                "message": "Token has expired"
            }), 401

        except jwt.InvalidTokenError:

            return jsonify({
                "status": "error",
                "message": "Invalid token"
            }), 401

        return f(*args, **kwargs)

    return decorated
