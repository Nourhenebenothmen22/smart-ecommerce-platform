FROM python:3.11-slim

WORKDIR /app

# psycopg2-binary ships its own libpq - no system deps needed

COPY ml/requirements-api.txt ./requirements.txt
RUN pip install --default-timeout=120 --retries=5 --no-cache-dir -r requirements.txt

COPY ml/ ./

RUN addgroup --system --gid 1001 python && \
    adduser --system --uid 1001 mluser && \
    chown -R mluser:python /app

USER mluser
EXPOSE 8000

ENV PYTHONPATH=/app
ENV SENTENCE_TRANSFORMERS_HOME=/app/model_cache
ENV ML_ALLOW_MODEL_DOWNLOADS=false

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
