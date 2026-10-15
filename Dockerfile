FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AUDIT_DATA_DIR=/var/lib/audit/runs
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt
COPY webapp ./webapp
COPY scripts ./scripts
COPY .claude/skills ./.claude/skills
COPY .claude/agents ./.claude/agents
COPY data ./data
COPY evidence/source-manifest.json ./evidence/source-manifest.json
COPY outputs/rules.json outputs/history.json ./outputs/
RUN useradd --create-home --uid 10001 audit && mkdir -p /var/lib/audit/runs && chown -R audit:audit /var/lib/audit
USER audit
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request,os; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/healthz',timeout=3)"
CMD ["python", "-m", "webapp"]
