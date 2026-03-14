#!/usr/bin/env python3
"""
deploy-python-app — A Python app that's already configured to deploy everywhere.

This app runs locally AND deploys to Docker, Railway, Fly.io, Render, or any
container platform with zero config changes. Everything is pre-wired.

Usage:
    python3 app.py                          # Run locally (port 8000)
    docker build -t myapp . && docker run -p 8000:8000 myapp  # Docker
    railway up                              # Railway
    fly deploy                              # Fly.io

The app includes:
    GET  /           — Health check + status page
    GET  /health     — JSON health endpoint (for platform health checks)
    GET  /api/hello  — Example API endpoint
    POST /api/echo   — Echo back JSON body
    GET  /api/env    — Show safe environment info (no secrets)
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ── Configuration (all via environment variables) ───────────────────────

PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")
APP_NAME = os.environ.get("APP_NAME", "my-python-app")
APP_ENV = os.environ.get("APP_ENV", "development")  # development, staging, production
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

# Track uptime
START_TIME = time.time()


# ── Request Handler ─────────────────────────────────────────────────────

class AppHandler(BaseHTTPRequestHandler):
    """HTTP request handler with routing."""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        routes = {
            "/": self.handle_index,
            "/health": self.handle_health,
            "/api/hello": self.handle_hello,
            "/api/env": self.handle_env,
        }

        handler = routes.get(path)
        if handler:
            handler(query)
        else:
            self.send_json(404, {"error": "Not found", "path": path})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/echo":
            self.handle_echo()
        else:
            self.send_json(404, {"error": "Not found", "path": path})

    # ── Route Handlers ──────────────────────────────────────────────────

    def handle_index(self, query):
        """Status page — proves the app is running."""
        uptime = time.time() - START_TIME
        html = f"""<!DOCTYPE html>
<html>
<head><title>{APP_NAME}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
.status {{ color: #22c55e; font-weight: bold; }}
code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }}
pre {{ background: #f1f5f9; padding: 16px; border-radius: 8px; overflow-x: auto; }}
h1 {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
</style>
</head>
<body>
<h1>{APP_NAME}</h1>
<p class="status">Running</p>
<p>Environment: <code>{APP_ENV}</code></p>
<p>Uptime: <code>{uptime:.0f}s</code></p>
<p>Python: <code>{sys.version.split()[0]}</code></p>

<h2>API Endpoints</h2>
<pre>
GET  /health      Health check (JSON)
GET  /api/hello   Hello endpoint
POST /api/echo    Echo back JSON body
GET  /api/env     Environment info
</pre>

<h2>Deploy This App</h2>
<pre>
# Docker
docker build -t {APP_NAME} . && docker run -p 8000:8000 {APP_NAME}

# Railway
railway up

# Fly.io
fly deploy
</pre>

<p><small>Built with <a href="https://github.com/LuciferForge/deploy-python-app">deploy-python-app</a></small></p>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def handle_health(self, query):
        """Health check endpoint — required by most platforms."""
        uptime = time.time() - START_TIME
        self.send_json(200, {
            "status": "healthy",
            "app": APP_NAME,
            "env": APP_ENV,
            "uptime_seconds": round(uptime, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "python": sys.version.split()[0],
        })

    def handle_hello(self, query):
        """Example API endpoint."""
        name = query.get("name", ["world"])[0]
        self.send_json(200, {
            "message": f"Hello, {name}!",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def handle_echo(self):
        """Echo back the request body."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self.send_json(400, {"error": "Empty body. Send JSON."})
            return
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
            self.send_json(200, {"echo": data, "received_at": datetime.now(timezone.utc).isoformat()})
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON"})

    def handle_env(self, query):
        """Show safe environment info (never expose secrets)."""
        SAFE_VARS = ["APP_NAME", "APP_ENV", "PORT", "HOST", "PYTHON_VERSION",
                     "RAILWAY_ENVIRONMENT", "FLY_APP_NAME", "RENDER_SERVICE_NAME",
                     "RAILWAY_PUBLIC_DOMAIN", "FLY_REGION", "RENDER_EXTERNAL_HOSTNAME"]
        env_info = {}
        for var in SAFE_VARS:
            val = os.environ.get(var)
            if val:
                env_info[var] = val
        env_info["python"] = sys.version.split()[0]
        env_info["platform"] = _detect_platform()
        self.send_json(200, env_info)

    # ── Helpers ─────────────────────────────────────────────────────────

    def send_json(self, status, data):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")  # CORS
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        """Custom log format."""
        if DEBUG:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}", file=sys.stderr)


# ── Platform Detection ──────────────────────────────────────────────────

def _detect_platform():
    """Detect which platform we're running on."""
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        return "railway"
    if os.environ.get("FLY_APP_NAME"):
        return "fly.io"
    if os.environ.get("RENDER_SERVICE_NAME"):
        return "render"
    if os.environ.get("DYNO"):
        return "heroku"
    if os.path.exists("/.dockerenv"):
        return "docker"
    return "local"


# ── Main ────────────────────────────────────────────────────────────────

def main():
    platform = _detect_platform()
    print(f"Starting {APP_NAME} ({APP_ENV})", file=sys.stderr)
    print(f"  Platform: {platform}", file=sys.stderr)
    print(f"  Listening: http://{HOST}:{PORT}", file=sys.stderr)
    print(f"  Health: http://{HOST}:{PORT}/health", file=sys.stderr)

    if SECRET_KEY == "change-me-in-production" and APP_ENV == "production":
        print("  WARNING: Set SECRET_KEY in production!", file=sys.stderr)

    server = HTTPServer((HOST, PORT), AppHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", file=sys.stderr)
        server.server_close()


if __name__ == "__main__":
    main()
