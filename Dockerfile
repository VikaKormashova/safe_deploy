FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

COPY . .

RUN addgroup --system appuser && \
    adduser --system --no-create-home --ingroup appuser appuser && \
    chown -R appuser:appuser /app && \
    chmod 755 /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
