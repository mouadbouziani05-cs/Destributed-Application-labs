from __future__ import annotations

from datetime import datetime
from typing import Any

import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for

from src.common.config import SETTINGS
from src.common.logging_utils import configure_service_logging


logger = configure_service_logging("web_ui")
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = SETTINGS.jwt_secret
app.config["MAX_CONTENT_LENGTH"] = SETTINGS.max_body_bytes


class GatewayClient:
    def __init__(self) -> None:
        self.base_url = SETTINGS.gateway_service_url.rstrip("/")
        self.session = requests.Session()

    def login(self, username: str, password: str) -> dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/api/login",
            json={"username": username, "password": password},
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def list_reports(self, token: str) -> list[dict[str, Any]]:
        response = self.session.get(
            f"{self.base_url}/api/reports",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        response.raise_for_status()
        return response.json().get("items", [])

    def get_report(self, token: str, report_id: str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/api/reports/{report_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def submit_report(self, token: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/api/reports",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def current_user(self, token: str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/api/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        response.raise_for_status()
        return response.json()


client = GatewayClient()


@app.context_processor
def inject_globals() -> dict[str, Any]:
    return {"now": datetime.utcnow()}


@app.get("/")
def index():
    return redirect(url_for("dashboard" if session.get("access_token") else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Identifiants invalides.", "error")
            return render_template("login.html")
        try:
            data = client.login(username, password)
            session["access_token"] = data["access_token"]
            session["current_user"] = data["user"]
            flash("Connexion réussie.", "success")
            return redirect(url_for("dashboard"))
        except requests.HTTPError:
            flash("Connexion refusée.", "error")
        except requests.RequestException:
            flash("Service indisponible pour le moment.", "error")
    return render_template("login.html")


@app.get("/logout")
def logout():
    session.clear()
    flash("Déconnexion effectuée.", "success")
    return redirect(url_for("login"))


@app.get("/dashboard")
def dashboard():
    token = session.get("access_token")
    if not token:
        return redirect(url_for("login"))
    try:
        current_user = client.current_user(token)
        reports = client.list_reports(token)
        session["current_user"] = current_user
        return render_template("dashboard.html", user=current_user, reports=reports)
    except requests.HTTPError:
        session.clear()
        flash("Session expirée, veuillez vous reconnecter.", "error")
        return redirect(url_for("login"))
    except requests.RequestException:
        flash("Impossible de charger l'historique.", "error")
        return render_template("dashboard.html", user=session.get("current_user", {}), reports=[])


@app.get("/admin/reports")
def admin_reports():
    token = session.get("access_token")
    if not token:
        return redirect(url_for("login"))
    try:
        current_user = client.current_user(token)
        if current_user.get("role") != "admin":
            flash("Accès administrateur requis.", "error")
            return redirect(url_for("dashboard"))
        reports = client.list_reports(token)
        session["current_user"] = current_user
        return render_template("admin_reports.html", user=current_user, reports=reports)
    except requests.HTTPError:
        session.clear()
        flash("Session expirée, veuillez vous reconnecter.", "error")
        return redirect(url_for("login"))
    except requests.RequestException:
        flash("Impossible de charger tous les signalements.", "error")
        return render_template("admin_reports.html", user=session.get("current_user", {}), reports=[])


@app.route("/submit", methods=["GET", "POST"])
def submit():
    token = session.get("access_token")
    if not token:
        return redirect(url_for("login"))
    if request.method == "POST":
        sender = request.form.get("sender", "").strip()
        subject = request.form.get("subject", "").strip()
        content = request.form.get("content", "").strip()
        attachments_raw = request.form.get("attachments", "")
        attachments = [item.strip() for item in attachments_raw.split(",") if item.strip()]
        try:
            report = client.submit_report(
                token,
                {
                    "sender": sender,
                    "subject": subject,
                    "content": content,
                    "attachments": attachments,
                },
            )
            flash(f"Signalement enregistré avec un score {report['score']} ({report['risk_level']}).", "success")
            return redirect(url_for("dashboard"))
        except requests.HTTPError:
            flash("Signalement refusé par la plateforme.", "error")
        except requests.RequestException:
            flash("Analyse indisponible.", "error")
    return render_template("submit.html", preset=request.form)


@app.get("/reports/<report_id>")
def report_detail(report_id: str):
    token = session.get("access_token")
    if not token:
        return redirect(url_for("login"))
    try:
        report = client.get_report(token, report_id)
        return render_template("report_detail.html", report=report)
    except requests.HTTPError:
        flash("Signalement introuvable ou non autorisé.", "error")
        return redirect(url_for("dashboard"))
    except requests.RequestException:
        flash("Impossible de charger le détail.", "error")
        return redirect(url_for("dashboard"))


@app.errorhandler(413)
def request_too_large(_: Exception):
    return render_template("error.html", title="Requête trop grande", message="Le contenu envoyé dépasse la limite autorisée."), 413


@app.errorhandler(404)
def not_found(_: Exception):
    return render_template("error.html", title="Page introuvable", message="La ressource demandée n'existe pas."), 404


@app.errorhandler(500)
def internal_error(_: Exception):
    return render_template("error.html", title="Erreur interne", message="Un problème est survenu côté interface."), 500
