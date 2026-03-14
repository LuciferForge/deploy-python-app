FROM python:3.11-slim

WORKDIR /app

# No requirements.txt needed — zero dependencies
COPY app.py .

# Railway, Render, Fly all use PORT env var
ENV PORT=8000
ENV APP_ENV=production

EXPOSE 8000

# Health check for container orchestrators
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python3", "app.py"]
