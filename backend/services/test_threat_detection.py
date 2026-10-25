from threat_detection_service import analyze_message


message = """
Your bank account will be blocked today.
Verify your KYC immediately by clicking this link:
https://example.com/verify
Enter your OTP to complete verification.
"""


result = analyze_message(message)

print(result)