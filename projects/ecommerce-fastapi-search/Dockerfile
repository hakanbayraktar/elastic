FROM python:3.12-slim

WORKDIR /workspace

# Sistem bağımlılıkları ve curl
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV HOST="0.0.0.0"
ENV PORT=19001
ENV PYTHONUNBUFFERED=1

EXPOSE 19001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "19001"]
