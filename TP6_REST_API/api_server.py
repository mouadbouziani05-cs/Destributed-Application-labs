import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

tickets_db = {}

API_TOKEN = "my-secure-token-2026"

class APIHandler(BaseHTTPRequestHandler):

    def _send_json(self, status_code, data):
        response = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _check_auth(self):
        auth = self.headers.get("Authorization", "")

        if auth != f"Bearer {API_TOKEN}":
            self._send_json(401, {
                "error": "unauthorized",
                "message": "Invalid or missing token"
            })
            return False

        return True

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {
                "status": "ok",
                "timestamp": datetime.utcnow().isoformat(),
                "tickets_count": len(tickets_db)
            })
            return

        self._send_json(404, {
            "error": "not_found",
            "message": "Endpoint not found"
        })

    def do_POST(self):
        if self.path != "/tickets":
            self._send_json(404, {
                "error": "not_found",
                "message": "Endpoint not found"
            })
            return

        if not self._check_auth():
            return

        content_length = int(self.headers.get("Content-Length", 0))

        if content_length == 0:
            self._send_json(400, {
                "error": "bad_request",
                "message": "Empty request body"
            })
            return

        try:
            raw_body = self.rfile.read(content_length)
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_json(400, {
                "error": "bad_request",
                "message": "Invalid JSON"
            })
            return

        subject = body.get("subject", "").strip()
        description = body.get("description", "").strip()

        if not subject or not description:
            self._send_json(400, {
                "error": "validation_error",
                "message": "subject and description are required"
            })
            return

        if len(subject) > 150:
            self._send_json(400, {
                "error": "validation_error",
                "message": "subject is too long"
            })
            return

        ticket_id = str(uuid.uuid4())

        tickets_db[ticket_id] = {
            "id": ticket_id,
            "subject": subject,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }

        self._send_json(201, tickets_db[ticket_id])

    def log_message(self, format, *args):
        print(f"[API] {self.address_string()} - {format % args}")

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8080), APIHandler)
    print("API server running at http://127.0.0.1:8080")
    print("Endpoints: GET /health, POST /tickets")
    server.serve_forever()