FROM python:3.11-slim

ARG AGENT_NAME
ENV AGENT_NAME=${AGENT_NAME}

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

COPY agents/python/base/ agents/python/base/
COPY agents/python/${AGENT_NAME}/ agents/python/${AGENT_NAME}/

RUN pip install --no-cache-dir \
    -r agents/python/${AGENT_NAME}/requirements.txt \
    && pip install --no-cache-dir -e agents/python/base

ENV PYTHONPATH=/app/agents/python

CMD python -m agents.python.${AGENT_NAME}.agent
