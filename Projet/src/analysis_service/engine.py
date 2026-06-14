from __future__ import annotations

from dataclasses import asdict, dataclass
import ipaddress
import re
from urllib.parse import urlparse

from src.common.errors import ValidationRejected
from src.common.validation import ReportSubmissionInput


URL_PATTERN = re.compile(r'https?://[^\s<>"]+', re.IGNORECASE)
IP_HOST_PATTERN = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")

URGENT_TERMS = {
    "urgent",
    "immediate",
    "act now",
    "final notice",
    "verify",
    "suspended",
    "payment failed",
    "account locked",
    "security alert",
    "update your information",
}

CREDENTIAL_TERMS = {
    "password",
    "login",
    "sign in",
    "authentication",
    "credentials",
    "confirm your account",
}

SHORTENER_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "cutt.ly",
    "lnkd.in",
    "rebrand.ly",
    "ow.ly",
}

FREE_MAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "proton.me",
    "protonmail.com",
}

SUSPICIOUS_ATTACHMENT_EXTENSIONS = {
    ".exe",
    ".js",
    ".vbs",
    ".scr",
    ".bat",
    ".cmd",
    ".ps1",
    ".zip",
    ".rar",
    ".iso",
    ".lnk",
    ".docm",
    ".xlsm",
}


@dataclass(frozen=True)
class Finding:
    code: str
    points: int
    label: str
    explanation: str


class AnalysisEngine:
    analysis_version = "1.0"

    def analyze_email(self, payload: dict) -> dict:
        request = ReportSubmissionInput.model_validate(payload)
        content = f"{request.subject}\n{request.content}"
        lower_content = content.lower()
        sender_domain = extract_registered_domain(request.sender.split("@", 1)[-1])
        urls = extract_urls(content)

        findings: list[Finding] = []

        urgent_hits = [term for term in URGENT_TERMS if term in lower_content]
        if urgent_hits:
            points = min(25, 6 * len(urgent_hits))
            findings.append(
                Finding(
                    code="urgent_language",
                    points=points,
                    label="Langage urgent ou coercitif",
                    explanation=f"Mots détectés: {', '.join(sorted(urgent_hits))}.",
                )
            )

        credential_hits = [term for term in CREDENTIAL_TERMS if term in lower_content]
        if credential_hits:
            points = min(20, 5 * len(credential_hits))
            findings.append(
                Finding(
                    code="credential_request",
                    points=points,
                    label="Demande de connexion ou de vérification",
                    explanation=f"Indices de demande d'identifiants: {', '.join(sorted(credential_hits))}.",
                )
            )

        suspicious_urls = []
        url_domains = []
        for raw_url in urls:
            parsed = urlparse(raw_url)
            hostname = (parsed.hostname or "").lower()
            if not hostname:
                continue
            url_domain = extract_registered_domain(hostname)
            url_domains.append(url_domain)
            if is_suspicious_url(hostname):
                suspicious_urls.append(raw_url)
        if suspicious_urls:
            points = min(35, 12 * len(suspicious_urls))
            findings.append(
                Finding(
                    code="suspicious_urls",
                    points=points,
                    label="URLs suspectes",
                    explanation=f"{len(suspicious_urls)} URL(s) à risque détectée(s).",
                )
            )

        if urls and sender_domain and url_domains:
            distinct_domains = {domain for domain in url_domains if domain}
            incoherent_domains = [domain for domain in distinct_domains if domain != sender_domain]
            if incoherent_domains and (credential_hits or suspicious_urls):
                findings.append(
                    Finding(
                        code="domain_mismatch",
                        points=20,
                        label="Incohérence de domaine",
                        explanation=(
                            f"Le domaine expéditeur '{sender_domain}' ne correspond pas aux domaines des liens: "
                            f"{', '.join(sorted(distinct_domains))}."
                        ),
                    )
                )

        suspicious_attachments = [item for item in request.attachments if is_suspicious_attachment(item)]
        if suspicious_attachments:
            points = min(30, 15 * len(suspicious_attachments))
            findings.append(
                Finding(
                    code="suspicious_attachments",
                    points=points,
                    label="Pièces jointes suspectes",
                    explanation=f"Extensions sensibles détectées: {', '.join(suspicious_attachments)}.",
                )
            )

        if sender_domain in FREE_MAIL_DOMAINS and (credential_hits or suspicious_urls):
            findings.append(
                Finding(
                    code="free_mail_impersonation",
                    points=10,
                    label="Adresse expéditrice peu crédible",
                    explanation=f"Le message provient d'un service de messagerie grand public: {sender_domain}.",
                )
            )

        score = min(100, sum(finding.points for finding in findings))
        risk_level = "low"
        if score >= 70:
            risk_level = "high"
        elif score >= 35:
            risk_level = "medium"

        justifications = [
            f"{finding.label} (+{finding.points}): {finding.explanation}" for finding in findings
        ]
        if not justifications:
            justifications.append("Aucun motif fort de phishing n'a été détecté.")

        return {
            "risk_score": score,
            "risk_level": risk_level,
            "justification": "\n".join(f"- {item}" for item in justifications),
            "urls_detected": urls,
            "signals": [asdict(finding) for finding in findings],
            "analysis_version": self.analysis_version,
        }


def extract_urls(text: str) -> list[str]:
    return sorted(set(URL_PATTERN.findall(text)))


def is_suspicious_url(hostname: str) -> bool:
    if IP_HOST_PATTERN.match(hostname):
        return True
    if hostname in SHORTENER_DOMAINS:
        return True
    if hostname.startswith("xn--"):
        return True
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def is_suspicious_attachment(filename: str) -> bool:
    lowered = filename.lower().strip()
    return any(lowered.endswith(extension) for extension in SUSPICIOUS_ATTACHMENT_EXTENSIONS)


def extract_registered_domain(hostname: str) -> str:
    host = hostname.lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = [part for part in host.split(".") if part]
    if len(parts) <= 2:
        return host
    if len(parts) >= 3 and len(parts[-1]) == 2 and len(parts[-2]) <= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])
