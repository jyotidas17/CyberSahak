import logging
import re
import hashlib
import secrets
from urllib.parse import urlencode

from flask import Blueprint, jsonify, request
from psycopg2 import errors

from db import get_db_connection
from config import Config
from middleware.auth_middleware import token_required
from services.auth_service import generate_token, hash_password, verify_password
from services.email_service import password_reset_email_configured, send_password_reset_email

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
log = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def json_object():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@auth_bp.route("/profile", methods=["GET"])
@token_required
def profile():
    user = request.user
    return jsonify({"status": "success", "user": {
        "id": user.get("user_id"), "email": user.get("email"), "role": user.get("role")
    }})


@auth_bp.route("/register", methods=["POST"])
def register():
    data = json_object()
    if data is None:
        return jsonify({"status": "error", "message": "A JSON request body is required"}), 400
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    if not all(isinstance(value, str) for value in (name, email, password)):
        return jsonify({"status": "error", "message": "Name, email and password are required"}), 400
    name, email, password = name.strip(), email.strip().lower(), password
    if not name or len(name) > 100 or not EMAIL_RE.fullmatch(email) or len(email) > 150:
        return jsonify({"status": "error", "message": "Enter a valid name and email address"}), 400
    if len(password) < 8 or len(password.encode("utf-8")) > 72:
        return jsonify({"status": "error", "message": "Password must be at least 8 characters and no more than 72 UTF-8 bytes"}), 400
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE lower(email) = %s", (email,))
            if cursor.fetchone():
                return jsonify({"status": "error", "message": "Email already registered"}), 409
            cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                           (name, email, hash_password(password)))
            user_id = cursor.fetchone()[0]
        connection.commit()
        return jsonify({"status": "success", "message": "User registered successfully", "user_id": user_id}), 201
    except errors.UniqueViolation:
        if connection:
            connection.rollback()
        return jsonify({"status": "error", "message": "Email already registered"}), 409
    except Exception:
        if connection:
            connection.rollback()
        log.exception("Registration failed")
        return jsonify({"status": "error", "message": "Registration failed"}), 500
    finally:
        if connection:
            connection.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = json_object()
    if data is None:
        return jsonify({"status": "error", "message": "A JSON request body is required"}), 400
    email, password = data.get("email"), data.get("password")
    if not isinstance(email, str) or not isinstance(password, str) or not email.strip() or not password:
        return jsonify({"status": "error", "message": "Email and password are required"}), 400
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, email, password_hash, role FROM users WHERE lower(email) = %s",
                           (email.strip().lower(),))
            user = cursor.fetchone()
        if not user or not verify_password(password, user[3]):
            return jsonify({"status": "error", "message": "Invalid email or password"}), 401
        token = generate_token(user[0], user[2], user[4])
        return jsonify({"status": "success", "message": "Login successful", "token": token,
                        "user": {"id": user[0], "name": user[1], "email": user[2], "role": user[4]}})
    except Exception:
        log.exception("Login failed")
        return jsonify({"status": "error", "message": "Login failed"}), 500
    finally:
        if connection:
            connection.close()


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = json_object()
    email = data.get("email") if data else None
    if not isinstance(email, str) or len(email.strip()) > 150 or not EMAIL_RE.fullmatch(email.strip()):
        return jsonify({"status": "error", "message": "Enter a valid email address"}), 400
    if not password_reset_email_configured():
        return jsonify({"status": "error", "message": "Password reset email is not configured yet. Please contact the project administrator."}), 503

    normalized_email = email.strip().lower()
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, email FROM users WHERE lower(email) = %s", (normalized_email,))
            user = cursor.fetchone()
            if not user:
                connection.commit()
                return jsonify({"status": "success", "message": "If an account exists for that email, a reset link will be sent."})

            user_id, recipient = user
            cursor.execute("""SELECT 1 FROM password_reset_tokens
                WHERE user_id = %s AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 minute'
                LIMIT 1""", (user_id,))
            if cursor.fetchone():
                connection.commit()
                return jsonify({"status": "success", "message": "If an account exists for that email, a reset link will be sent."})

            cursor.execute("UPDATE password_reset_tokens SET used_at = CURRENT_TIMESTAMP WHERE user_id = %s AND used_at IS NULL", (user_id,))
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
            cursor.execute("""INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP + INTERVAL '30 minutes')""", (user_id, token_hash))
            reset_url = f"{Config.FRONTEND_ORIGIN.rstrip('/')}/reset-password?{urlencode({'token': raw_token})}"
            send_password_reset_email(recipient, reset_url)
        connection.commit()
        return jsonify({"status": "success", "message": "If an account exists for that email, a reset link will be sent."})
    except Exception:
        if connection:
            connection.rollback()
        log.exception("Password reset email could not be sent")
        # Keep the same response for existing and non-existing accounts.
        return jsonify({"status": "success", "message": "If an account exists for that email, a reset link will be sent."})
    finally:
        if connection:
            connection.close()


@auth_bp.route("/demo-reset-password", methods=["POST"])
def demo_reset_password():
    if not Config.ALLOW_DEMO_PASSWORD_RESET:
        return jsonify({"status": "error", "message": "Direct password reset is disabled. Use the verified recovery link."}), 403

    data = json_object()
    email = data.get("email") if data else None
    password = data.get("password") if data else None
    if not isinstance(email, str) or not EMAIL_RE.fullmatch(email.strip()) or len(email.strip()) > 150:
        return jsonify({"status": "error", "message": "Enter a valid account email address"}), 400
    if not isinstance(password, str) or len(password) < 8 or len(password.encode("utf-8")) > 72:
        return jsonify({"status": "error", "message": "Password must be at least 8 characters and no more than 72 UTF-8 bytes"}), 400

    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("UPDATE users SET password_hash = %s WHERE lower(email) = %s RETURNING id",
                           (hash_password(password), email.strip().lower()))
            updated_user = cursor.fetchone()
        if not updated_user:
            connection.rollback()
            return jsonify({"status": "error", "message": "No account was found for that email address"}), 404
        connection.commit()
        return jsonify({"status": "success", "message": "Password updated. You can now sign in with your new password."})
    except Exception:
        if connection:
            connection.rollback()
        log.exception("Demo password reset failed")
        return jsonify({"status": "error", "message": "Password could not be updated. Please try again."}), 500
    finally:
        if connection:
            connection.close()


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = json_object()
    if data is None:
        return jsonify({"status": "error", "message": "A JSON request body is required"}), 400
    token, password = data.get("token"), data.get("password")
    if not isinstance(token, str) or not token or len(token) > 200:
        return jsonify({"status": "error", "message": "Reset link is invalid or expired. Request a new one."}), 400
    if not isinstance(password, str) or len(password) < 8 or len(password.encode("utf-8")) > 72:
        return jsonify({"status": "error", "message": "Password must be at least 8 characters and no more than 72 UTF-8 bytes"}), 400

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""SELECT user_id FROM password_reset_tokens
                WHERE token_hash = %s AND expires_at > CURRENT_TIMESTAMP AND used_at IS NULL
                FOR UPDATE""", (token_hash,))
            row = cursor.fetchone()
            if not row:
                connection.rollback()
                return jsonify({"status": "error", "message": "Reset link is invalid or expired. Request a new one."}), 400
            user_id = row[0]
            cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hash_password(password), user_id))
            cursor.execute("UPDATE password_reset_tokens SET used_at = CURRENT_TIMESTAMP WHERE user_id = %s AND used_at IS NULL", (user_id,))
        connection.commit()
        return jsonify({"status": "success", "message": "Password reset successfully. Please sign in with your new password."})
    except Exception:
        if connection:
            connection.rollback()
        log.exception("Password reset failed")
        return jsonify({"status": "error", "message": "Password could not be reset. Please request a new link."}), 500
    finally:
        if connection:
            connection.close()
