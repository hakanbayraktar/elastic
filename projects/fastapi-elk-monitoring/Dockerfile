FROM python:3.12-slim

WORKDIR /app

# Sistem gereksinimleri (curl vs.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/

EXPOSE 19002

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=19002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "19002"]
