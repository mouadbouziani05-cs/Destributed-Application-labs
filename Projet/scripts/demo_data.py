from __future__ import annotations

PHISHING_SAMPLES = [
    {
        "sender": "security-alerts@microsooft-support.com",
        "subject": "Action immediate required: account suspended",
        "content": (
            "Your account is locked. Verify your password immediately at https://bit.ly/secure-login "
            "to avoid permanent loss of access."
        ),
        "attachments": ["invoice.zip"],
    },
    {
        "sender": "billing@bank-example.com",
        "subject": "Payment failed - urgent update needed",
        "content": (
            "We could not process your payment. Sign in now at http://192.168.0.42/update to confirm your credentials."
        ),
        "attachments": ["readme.txt"],
    },
    {
        "sender": "hr@company-helpdesk.com",
        "subject": "Final notice: document review",
        "content": (
            "Please open the attached file and confirm your login details before 18:00."
        ),
        "attachments": ["review.docm"],
    },
]
