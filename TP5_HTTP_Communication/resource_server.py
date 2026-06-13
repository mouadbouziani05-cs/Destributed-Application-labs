import json
import time
import random
from http.server import HTTPServer, BaseHTTPRequestHandler

FILES = {
    "101": {"id": 101, "name": "Network Report", "owner": "Admin"},
    "102": {"id": 102, "name": "Security Audit", "owner": "Manager"},
    "103": {"id": 103, "name": "Cloud Notes", "owner": "Student"},
}

class ResourceHandler(BaseHTTPRequestHandler):

    def _send_json(self, code, data):
        response = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def do_GET(self):
        latency = random.uniform(0, 2)
        print(f"Simulated latency: {latency:.2f}s")
        time.sleep(latency)

        parts = self.path.strip("/").split("/")

        if parts[0] == "files":
            if len(parts) == 1:
                self._send_json(200, list(FILES.values()))
            elif len(parts) == 2 and parts[1] in FILES:
                self._send_json(200, FILES[parts[1]])
            else:
                self._send_json(404, {"error": "File not found"})
        else:
            self._send_json(404, {"error": "Unknown route"})

    def do_POST(self):
        self._send_json(405, {"error": "Method not allowed"})

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), ResourceHandler)
    print("Server running at http://127.0.0.1:8000")
    print("Try: /files or /files/101")
    server.serve_forever()