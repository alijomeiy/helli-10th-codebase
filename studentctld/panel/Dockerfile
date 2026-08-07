FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    TZ=Asia/Tehran \
    PIP_NO_CACHE_DIR=1

# tzdata -> correct open-hours matching; openssh-client -> ssh-keygen in entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
        tzdata openssh-client ca-certificates \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN chmod +x /app/entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "app:app"]
