from __future__ import annotations

import bootstrap  # noqa: F401

import requests

from scripts.demo_data import PHISHING_SAMPLES
from src.common.config import SETTINGS


BASE_URL = SETTINGS.gateway_service_url.rstrip("/")


def main() -> None:
    session = requests.Session()
    login = session.post(
        f"{BASE_URL}/api/login",
        json={"username": "analyst", "password": "User!2345"},
        timeout=5,
    )
    login.raise_for_status()
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    for index, sample in enumerate(PHISHING_SAMPLES, start=1):
        response = session.post(f"{BASE_URL}/api/reports", json=sample, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"[{index}] {data['report_id']} -> score {data['score']} ({data['risk_level']})")


if __name__ == "__main__":
    main()
