"""Database-backed smoke/regression tests. Uses and removes only unique test accounts."""
import time
import unittest
import uuid

import jwt

from app import create_app
from config import Config
from db import get_db_connection


class ApiIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({"TESTING": True})
        cls.client = cls.app.test_client()
        cls.email = f"cybersahak-test-{uuid.uuid4().hex}@example.invalid"
        cls.other_email = f"cybersahak-test-{uuid.uuid4().hex}@example.invalid"
        cls.password = "Test-Only-Password-934!"

    @classmethod
    def tearDownClass(cls):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE email IN (%s, %s)", (cls.email, cls.other_email))
            connection.commit()
        finally:
            connection.close()

    def auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_auth_analysis_persistence_dashboard_and_isolation(self):
        self.assertEqual(self.client.post("/api/auth/register", json={}).status_code, 400)
        first = self.client.post("/api/auth/register", json={"name": "Test User", "email": self.email.upper(), "password": self.password})
        self.assertEqual(first.status_code, 201)
        self.assertEqual(self.client.post("/api/auth/register", json={"name": "Again", "email": self.email, "password": self.password}).status_code, 409)
        login = self.client.post("/api/auth/login", json={"email": self.email, "password": self.password})
        self.assertEqual(login.status_code, 200)
        token = login.get_json()["token"]
        self.assertEqual(self.client.post("/api/auth/login", json={"email": self.email, "password": "wrong-pass"}).status_code, 401)
        self.assertEqual(self.client.get("/api/auth/profile").status_code, 401)
        self.assertEqual(self.client.get("/api/auth/profile", headers=self.auth("bad.token.value")).status_code, 401)
        expired = jwt.encode({"user_id": 999999, "email": self.email, "role": "user", "exp": int(time.time()) - 1}, Config.JWT_SECRET, algorithm="HS256")
        self.assertEqual(self.client.get("/api/auth/profile", headers=self.auth(expired)).status_code, 401)
        self.assertEqual(self.client.get("/api/auth/profile", headers=self.auth(token)).status_code, 200)
        self.assertEqual(self.client.post("/api/analysis/message", json={}, headers=self.auth(token)).status_code, 400)
        message = self.client.post("/api/analysis/message", json={"message": "Your bank account will be suspended. Verify your KYC immediately and send your OTP at https://example.com"}, headers=self.auth(token))
        self.assertEqual(message.status_code, 200, message.get_json())
        analysis_id = message.get_json()["analysis"]["analysis_id"]
        self.assertGreaterEqual(message.get_json()["analysis"]["risk_score"], 60)
        from services.ml_classifier import is_available
        if is_available():
            self.assertEqual(message.get_json()["analysis"]["detection_method"], "rules+local_ml")
            self.assertEqual(message.get_json()["analysis"]["model_version"], "sms-spam-uci-v1")
        url = self.client.post("/api/analysis/url", json={"url": "http://127.0.0.1:8080/login"}, headers=self.auth(token))
        self.assertEqual(url.status_code, 200, url.get_json())
        self.assertEqual(self.client.post("/api/analysis/url", json={"url": "javascript:alert(1)"}, headers=self.auth(token)).status_code, 400)
        history = self.client.get("/api/analysis/history", headers=self.auth(token))
        self.assertEqual(history.status_code, 200)
        self.assertGreaterEqual(history.get_json()["total"], 2)
        self.assertEqual(self.client.get("/api/dashboard/summary", headers=self.auth(token)).get_json()["total"], 2)
        self.assertEqual(self.client.get(f"/api/analysis/{analysis_id}", headers=self.auth(token)).status_code, 200)
        second = self.client.post("/api/auth/register", json={"name": "Other User", "email": self.other_email, "password": self.password})
        self.assertEqual(second.status_code, 201)
        other_token = self.client.post("/api/auth/login", json={"email": self.other_email, "password": self.password}).get_json()["token"]
        self.assertEqual(self.client.get(f"/api/analysis/{analysis_id}", headers=self.auth(other_token)).status_code, 404)
        self.assertEqual(self.client.get("/api/analysis/history", headers=self.auth(other_token)).get_json()["total"], 0)

    def test_url_edge_cases(self):
        from services.url_analysis_service import analyze_url
        self.assertEqual(analyze_url("https://example.com")["risk_level"], "LOW")
        self.assertTrue(analyze_url("http://127.0.0.1:8080/login")["indicators"])
        with self.assertRaises(ValueError):
            analyze_url("")
        with self.assertRaises(ValueError):
            analyze_url("javascript:alert(1)")

    def test_message_heuristic_signals_and_benign_text(self):
        from services.threat_detection_service import analyze_message
        benign = analyze_message("Thanks for sharing the meeting notes. See you tomorrow.")
        self.assertEqual(benign["risk_score"], 0)
        self.assertEqual(benign["risk_level"], "LOW")
        suspicious = analyze_message("Act now: your account will be suspended. Send your OTP to verify KYC.")
        self.assertGreaterEqual(suspicious["risk_score"], 60)
        self.assertTrue(all("evidence" in item for item in suspicious["indicators"]))

    def test_dev_cors_supports_both_loopback_hosts(self):
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            response = self.client.options("/api/auth/register", headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
            })
            self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), origin)

    def test_trained_local_spam_model(self):
        from services.ml_classifier import classify_spam_like, is_available
        if not is_available():
            self.skipTest("Train the local model before running this integration check")
        spam = classify_spam_like("FreeMsg: claim your reward now by replying to this number")
        benign = classify_spam_like("Hey, are we still meeting for lunch at six?")
        self.assertTrue(spam["is_spam_like"])
        self.assertFalse(benign["is_spam_like"])
        self.assertNotIn("confidence", spam)


if __name__ == "__main__":
    unittest.main()
