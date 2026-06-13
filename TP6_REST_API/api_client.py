import json
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def api_request(method, url, data=None, token=None, timeout=10):
    body_bytes = None

    if data is not None:
        body_bytes = json.dumps(data).encode("utf-8")

    request = Request(url, data=body_bytes, method=method)
    request.add_header("Content-Type", "application/json")

    request_id = str(uuid.uuid4())
    request.add_header("X-Request-Id", request_id)

    print(f"[{request_id[:8]}] {method} {url}")

    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
            print(f"Status: {response.status}")
            return response.status, body

    except HTTPError as e:
        try:
            error_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            error_body = {}

        print(f"HTTP Error {e.code}: {error_body}")
        return e.code, error_body

    except URLError as e:
        print(f"Network error: {e.reason}")
        return None, {"error": str(e.reason)}

if __name__ == "__main__":
    BASE_URL = "http://127.0.0.1:8080"
    TOKEN = "my-secure-token-2026"

    api_request("GET", f"{BASE_URL}/health")

    api_request(
        "POST",
        f"{BASE_URL}/tickets",
        data={
            "subject": "Connection problem",
            "description": "The distributed service is not responding"
        },
        token=TOKEN,
        timeout=5
    )

    api_request(
        "POST",
        f"{BASE_URL}/tickets",
        data={
            "subject": "Test without auth",
            "description": "This request should fail"
        }
    )