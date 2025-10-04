FROM debian:12-slim

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install postfix and other required packages including procps for ps command
RUN apt-get update && \
    apt-get install -y postfix mailutils python3 python3-pip sudo python3-venv curl procps && \
    rm -rf /var/lib/apt/lists/*

# Configure postfix for internet usage as a satellite system
RUN echo "postfix postfix/mailname string localhost" | debconf-set-selections && \
    echo "postfix postfix/main_cf_content string " | debconf-set-selections && \
    dpkg-reconfigure -f noninteractive postfix

# Create a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application files
COPY . /app
WORKDIR /app

# Make the entrypoint script executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Install Python dependencies in the virtual environment
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir requests flask

# Create necessary directories and set permissions
RUN mkdir -p /etc/postfix /var/spool/postfix /var/lib/postfix /var/run/postfix && \
    touch /etc/postfix/sasl_passwd && \
    touch /etc/postfix/sasl_passwd.db && \
    chmod 600 /etc/postfix/sasl_passwd* && \
    chmod +x /app/*.py && \
    chown -R root:root /etc/postfix /var/spool/postfix /var/lib/postfix /var/run/postfix

# Expose ports for web UI, API, and SMTP
EXPOSE 5000 5001 25

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]