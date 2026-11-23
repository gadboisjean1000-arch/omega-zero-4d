# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SUPELA_MODE=PRODUCTION_DETERMINISTIC

WORKDIR /app

# 0$ PMU : aucune dépendance externe (requirements.txt vide / stdlib pure)
COPY requirements.txt ./
COPY src/omega_zero/supela_agent_ready_engine.py src/omega_zero/server.py ./src/omega_zero/

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin supela
USER supela

EXPOSE 8080

CMD ["python", "src/omega_zero/server.py"]
