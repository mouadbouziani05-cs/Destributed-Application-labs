from src.analysis_service.engine import AnalysisEngine


def test_phishing_email_is_high_risk() -> None:
    engine = AnalysisEngine()
    result = engine.analyze_email(
        {
            "sender": "security-alerts@microsooft-support.com",
            "subject": "Immediate action required",
            "content": (
                "Your account is suspended. Verify your password at https://bit.ly/secure-login "
                "or access http://192.168.0.42/update now."
            ),
            "attachments": ["invoice.zip"],
        }
    )

    assert result["risk_level"] == "high"
    assert result["risk_score"] >= 70
    assert any(signal["code"] == "suspicious_urls" for signal in result["signals"])
    assert any(signal["code"] == "suspicious_attachments" for signal in result["signals"])


def test_benign_email_is_low_risk() -> None:
    engine = AnalysisEngine()
    result = engine.analyze_email(
        {
            "sender": "team@company.com",
            "subject": "Weekly report",
            "content": "Please find the report attached.",
            "attachments": ["report.pdf"],
        }
    )

    assert result["risk_level"] == "low"
    assert result["risk_score"] <= 20
