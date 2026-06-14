# Plateforme distribuée de détection et qualification d'e-mails de phishing

Mini plateforme locale en Python pour soumettre des e-mails suspects, les analyser de façon heuristique, calculer un score de risque et historiser les événements sensibles dans un environnement distribué réel.

## Architecture

- `AuthService` : authentification, hash bcrypt, émission et vérification de JWT, rôles `user` et `admin`.
- `SubmissionService / API Gateway` : point d'entrée REST, validation stricte, contrôle d'accès, journalisation des actions sensibles, consultation de l'historique.
- `AnalysisService` : service RPC Pyro5 qui applique les heuristiques de phishing et retourne le score et les justifications.
- `AuditService` : collecte les événements de sécurité en JSON structuré.
- `Client` : console interactive pour login, soumission et consultation.
- `Web UI` : mini interface Flask pour login, soumission et consultation dans le navigateur.

## Stack choisie

- `FastAPI` pour les services HTTP.
- `Pyro5` pour le RPC distribué entre le gateway et le moteur d'analyse.
- `SQLite` pour la persistance locale.
- `PyJWT` pour les jetons d'accès.
- `bcrypt` pour les mots de passe.
- `requests` pour les appels interservices HTTP.
- `logging` avec format JSON pour l'audit applicatif.

## Arborescence

```text
src/
  auth_service/
  audit_service/
  analysis_service/
  gateway/
      web_ui/
  client/
  common/
scripts/
tests/
```

## Diagramme des services

```text
[Console Client]
      |
      v
[Gateway REST - FastAPI] -----> [AuthService REST - FastAPI]
      |                                  |
      |                                  +--> logs sécurité vers AuditService
      |
      +---- RPC Pyro5 ----> [AnalysisService]
      |
      +---------------------> [AuditService REST - FastAPI]
```

## Flux de communication

1. Le client se connecte au gateway via `/api/login`.
2. Le gateway relaie l'authentification à l'AuthService.
3. Le client soumet un e-mail suspect via `/api/reports` avec un JWT Bearer.
4. Le gateway valide l'entrée, appelle l'AnalysisService via Pyro5, puis stocke le résultat dans SQLite.
5. Les actions sensibles sont journalisées par l'AuditService.
6. Le client consulte l'historique avec `/api/reports` et un JWT valide.

## Installation

```bash
python -m pip install -r requirements.txt
```

## Préparation des données de démonstration

```bash
python scripts/seed_demo.py
```

Cela crée les bases SQLite et les comptes de démonstration suivants :

- `admin` / `Admin!2345`
- `analyst` / `User!2345`

## Lancement des services

Dans quatre terminaux séparés :

```bash
python scripts/run_auth_service.py
```

```bash
python scripts/run_audit_service.py
```

```bash
python scripts/run_analysis_service.py
```

```bash
python scripts/run_gateway.py
```

## Lancement en une commande

```bash
python scripts/run_platform.py --seed
```

Cette commande initialise les données de démonstration puis démarre tous les services locaux, y compris l'interface web Flask.

## Utilisation du client console

```bash
python -m src.client.console
```

## Interface web Flask

```bash
python scripts/run_web_ui.py
```

L'interface est disponible sur `http://127.0.0.1:8501`.

## Endpoints principaux

### AuthService
- `POST /auth/login`
- `POST /auth/verify`
- `GET /health`

### Gateway
- `POST /api/login`
- `POST /api/reports`
- `GET /api/reports`
- `GET /api/reports/{report_id}`
- `GET /api/me`
- `GET /health`

### AuditService
- `POST /audit/events`
- `GET /audit/events`
- `GET /health`

## Sécurité

- Mots de passe hashés avec `bcrypt`.
- Jetons JWT signés et vérifiés.
- Validation stricte des entrées avec `Pydantic`.
- Taille maximale des requêtes contrôlée par middleware.
- Rate limiting simple côté gateway.
- Journaux structurés JSON, sans exposer les jetons complets.
- Appels distants avec timeouts et retry simple.
- Circuit breaker simplifié pour le RPC d'analyse.
- Contrôle de rôle pour la consultation de l'historique.

## Exemples de phishing

Le fichier `scripts/demo_data.py` contient trois exemples réalistes :
- urgence et usurpation de marque,
- URL courte ou IP brute,
- pièce jointe dangereuse.

## Tests

```bash
pytest -q
```
