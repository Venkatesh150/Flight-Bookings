FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=5000

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY --chown=app:app app.py ./
COPY --chown=app:app templates/ ./templates/
COPY --chown=app:app static/ ./static/

USER app

EXPOSE 5000

CMD ["python", "app.py"]
