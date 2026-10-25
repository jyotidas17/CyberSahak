import bcrypt
import jwt
from datetime import datetime, timedelta
from config import Config


def hash_password(password):
    password_bytes = password.encode("utf-8")

    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(
        password_bytes,
        salt
    )

    return hashed_password.decode("utf-8")


def verify_password(password, hashed_password):
    password_bytes = password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")

    return bcrypt.checkpw(
        password_bytes,
        hashed_bytes
    )


def generate_token(user_id, email, role):

    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }

    token = jwt.encode(
        payload,
        Config.JWT_SECRET,
        algorithm="HS256"
    )

    return token