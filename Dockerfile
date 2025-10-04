FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && \
    apt-get install -y postfix mailutils python3 python3-pip sudo curl procps rsyslog iputils-ping python3-venv && \
    rm -rf /var/lib/apt/lists/*

# Configure postfix
RUN echo "postfix postfix/mailname string localhost" | debconf-set-selections && \
    dpkg-reconfigure -f noninteractive postfix

# Backup original postfix configuration
RUN cp -a /etc/postfix /etc/postfix.bak

WORKDIR /app
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose ports
EXPOSE 8000 25

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]