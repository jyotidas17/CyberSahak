import smtplib
from email.message import EmailMessage

from config import Config


def password_reset_email_configured():
    return all((Config.SMTP_HOST, Config.SMTP_USERNAME, Config.SMTP_PASSWORD,
                Config.SMTP_FROM_EMAIL))


def send_password_reset_email(recipient, reset_url):
    message = EmailMessage()
    message["Subject"] = "Reset your CyberSahak password"
    message["From"] = Config.SMTP_FROM_EMAIL
    message["To"] = recipient
    message.set_content(
        "We received a request to reset your CyberSahak password.\n\n"
        f"Use this one-time link within 30 minutes:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email. Your password has not changed."
    )

    smtp_class = smtplib.SMTP_SSL if Config.SMTP_USE_SSL else smtplib.SMTP
    with smtp_class(Config.SMTP_HOST, Config.SMTP_PORT, timeout=12) as server:
        if Config.SMTP_USE_TLS and not Config.SMTP_USE_SSL:
            server.starttls()
        server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        server.send_message(message)
