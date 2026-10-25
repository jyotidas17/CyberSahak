"""Reset a CyberSahak account password from the local backend console."""

import getpass

from db import get_db_connection
from services.auth_service import hash_password


def main():
    email = input("Account email: ").strip().lower()
    if not email:
        print("Email is required.")
        return

    password = getpass.getpass("New account password (hidden): ")
    confirmation = getpass.getpass("Enter it again (hidden): ")
    if password != confirmation:
        print("Passwords do not match. No changes were made.")
        return
    if len(password) < 8 or len(password.encode("utf-8")) > 72:
        print("Password must be at least 8 characters and at most 72 UTF-8 bytes.")
        return

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE lower(email) = %s RETURNING id",
                (hash_password(password), email),
            )
            updated = cursor.fetchone()
        if not updated:
            connection.rollback()
            print("No account was found for that email. No changes were made.")
            return
        connection.commit()
        print("Password reset. Sign in with your new account password.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
