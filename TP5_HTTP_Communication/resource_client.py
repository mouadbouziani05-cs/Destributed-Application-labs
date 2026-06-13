import json
import time
import socket
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 1.5

def get_file(file_id):
    url = f"{BASE_URL}/files/{file_id}"
    print(f"\nRequest to {url}")

    start = time.time()

    try:
        response = urllib.request.urlopen(url, timeout=TIMEOUT)
        duration = time.time() - start

        data = json.loads(response.read().decode("utf-8"))
        print(f"Response received in {duration:.2f}s")
        print(data)
        return data

    except (urllib.error.URLError, socket.timeout) as e:
        duration = time.time() - start
        print(f"Network error or timeout after {duration:.2f}s: {e}")
        return None

if __name__ == "__main__":
    for i in range(5):
        get_file("101")