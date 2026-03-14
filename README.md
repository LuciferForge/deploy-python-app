# deploy-python-app

A Python app that's **already configured to deploy everywhere**. Docker, Railway, Fly.io, Render — zero config changes needed. Just deploy.

Built to solve the #1 problem developers hit with AI-generated code: **"It works locally but won't deploy."**

## Deploy in 60 Seconds

### Local
```bash
python3 app.py
# → http://localhost:8000
```

### Docker
```bash
docker build -t myapp .
docker run -p 8000:8000 myapp
# → http://localhost:8000
```

### Railway
```bash
railway login
railway init
railway up
# → https://your-app.railway.app
```

### Fly.io
```bash
fly auth login
fly launch    # Uses the included fly.toml
fly deploy
# → https://your-app.fly.dev
```

### Render
Push to GitHub → connect repo in Render dashboard → auto-deploys using `render.yaml`.

### Heroku
```bash
heroku create
git push heroku main
# Uses the included Procfile
```

## What's Included

```
app.py              ← Your app (single file, zero dependencies)
Dockerfile          ← Docker config with health check
docker-compose.yml  ← Local Docker development
fly.toml            ← Fly.io config
railway.json        ← Railway config
render.yaml         ← Render config
Procfile            ← Heroku config
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Status page (HTML) |
| GET | `/health` | Health check (JSON) — used by all platforms |
| GET | `/api/hello?name=World` | Example endpoint |
| POST | `/api/echo` | Echo back JSON body |
| GET | `/api/env` | Safe environment info |

## Add Your Own Code

The app is a single Python file. Add routes by adding methods to the handler:

```python
# In AppHandler class:

def handle_users(self, query):
    """Your custom endpoint."""
    self.send_json(200, {"users": ["alice", "bob"]})

# Register in do_GET:
routes = {
    "/": self.handle_index,
    "/health": self.handle_health,
    "/api/users": self.handle_users,  # ← Add here
}
```

## Add a Database

```python
import sqlite3

# In main():
db = sqlite3.connect("app.db")
db.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT)")

# In handler:
def handle_items(self, query):
    items = db.execute("SELECT * FROM items").fetchall()
    self.send_json(200, {"items": items})
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port (set automatically by most platforms) |
| `HOST` | `0.0.0.0` | Bind address |
| `APP_NAME` | `my-python-app` | App name shown in status page |
| `APP_ENV` | `development` | Environment (`development`, `staging`, `production`) |
| `DEBUG` | `false` | Enable debug logging |
| `SECRET_KEY` | `change-me...` | Your secret key (set in production!) |

## Why This Exists

Deploying a Python app should take 60 seconds, not 60 messages with AI debugging Dockerfile issues. This repo has every deployment config pre-written and tested so you can go from code to production without the debugging loop.

## Features

- **Zero dependencies** — just Python standard library
- **CORS enabled** — frontend can call API from any domain
- **Health check endpoint** — required by Railway, Fly, Render, Docker
- **Platform detection** — auto-detects Railway, Fly, Render, Heroku, Docker
- **Single file** — entire app in `app.py`, easy to understand and extend

## Requirements

- Python 3.6+
- No external packages

## License

MIT
