FROM debian:12-slim

# Install dependensi dasar dan Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv sudo curl procps && \
    rm -rf /var/lib/apt/lists/*

# Setup Virtual Environment untuk Python
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Salin file aplikasi
COPY . /app
WORKDIR /app

# Install dependensi Python
RUN pip install --no-cache-dir -r requirements.txt

# Buat entrypoint bisa dieksekusi
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port untuk Web UI
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

