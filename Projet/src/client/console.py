from __future__ import annotations

import getpass
from typing import Any

import requests

from src.common.config import SETTINGS


class ConsoleClient:
    def __init__(self) -> None:
        self.base_url = SETTINGS.gateway_service_url.rstrip("/")
        self.session = requests.Session()
        self.token: str | None = None

    def _headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def login(self) -> None:
        username = input("Identifiant: ").strip()
        password = getpass.getpass("Mot de passe: ")
        response = self.session.post(
            f"{self.base_url}/api/login",
            json={"username": username, "password": password},
            timeout=5,
        )
        if response.status_code != 200:
            print("Connexion refusée")
            return
        data = response.json()
        self.token = data["access_token"]
        print(f"Connecté en tant que {data['user']['username']} ({data['user']['role']})")

    def submit_report(self) -> None:
        if not self.token:
            print("Veuillez vous connecter d'abord")
            return
        sender = input("Expéditeur: ").strip()
        subject = input("Objet: ").strip()
        print("Contenu: saisissez plusieurs lignes, terminez par END")
        content_lines: list[str] = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            content_lines.append(line)
        attachments_raw = input("Pièces jointes séparées par des virgules (optionnel): ").strip()
        attachments = [item.strip() for item in attachments_raw.split(",") if item.strip()]
        response = self.session.post(
            f"{self.base_url}/api/reports",
            json={"sender": sender, "subject": subject, "content": "\n".join(content_lines), "attachments": attachments},
            headers=self._headers(),
            timeout=5,
        )
        if response.status_code != 200:
            print("Signalement refusé")
            return
        data = response.json()
        print(f"Signalement {data['report_id']} enregistré avec un score {data['score']} ({data['risk_level']})")
        print(data["justification"])

    def list_reports(self) -> None:
        if not self.token:
            print("Veuillez vous connecter d'abord")
            return
        response = self.session.get(f"{self.base_url}/api/reports", headers=self._headers(), timeout=5)
        if response.status_code != 200:
            print("Consultation refusée")
            return
        items = response.json().get("items", [])
        if not items:
            print("Aucun signalement")
            return
        for item in items:
            print(
                f"- {item['report_id']} | {item['created_at']} | {item['sender']} | {item['subject']} | score={item['score']} | {item['risk_level']}"
            )

    def show_report(self) -> None:
        if not self.token:
            print("Veuillez vous connecter d'abord")
            return
        report_id = input("Identifiant du signalement: ").strip()
        response = self.session.get(f"{self.base_url}/api/reports/{report_id}", headers=self._headers(), timeout=5)
        if response.status_code != 200:
            print("Signalement introuvable ou inaccessible")
            return
        data = response.json()
        print(f"Expéditeur: {data['sender']}")
        print(f"Objet: {data['subject']}")
        print(f"Score: {data['score']} ({data['risk_level']})")
        print("Justification:")
        print(data["justification"])


def main() -> None:
    client = ConsoleClient()
    actions = {
        "1": client.login,
        "2": client.submit_report,
        "3": client.list_reports,
        "4": client.show_report,
    }
    while True:
        print("\n1) Login")
        print("2) Soumettre un e-mail")
        print("3) Lister l'historique")
        print("4) Consulter un signalement")
        print("5) Quitter")
        choice = input("Choix: ").strip()
        if choice == "5":
            break
        action = actions.get(choice)
        if action is None:
            print("Choix invalide")
            continue
        action()


if __name__ == "__main__":
    main()
