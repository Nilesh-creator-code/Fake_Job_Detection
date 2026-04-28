from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from detector.pipeline import analyze_job_url

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"


class AppHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, path: Path, content_type: str) -> None:
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/":
            return self._send_file(FRONTEND_DIR / "index.html", "text/html; charset=utf-8")
        if route == "/styles.css":
            return self._send_file(FRONTEND_DIR / "styles.css", "text/css; charset=utf-8")
        if route == "/app.js":
            return self._send_file(FRONTEND_DIR / "app.js", "application/javascript; charset=utf-8")
        if route == "/api/health":
            return self._send_json({"status": "ok"})
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/analyze":
            return self._send_json({"error": "Not found"}, status=404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            url = (payload.get("url") or "").strip()
            if not url:
                return self._send_json({"error": "A URL is required."}, status=400)
            result = analyze_job_url(url)
            return self._send_json(result.to_dict())
        except Exception as exc:  # pragma: no cover
            return self._send_json({"error": "Analysis failed.", "details": str(exc)}, status=500)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Fake Job Detection dashboard running at http://{host}:{port}")
    server.serve_forever()
