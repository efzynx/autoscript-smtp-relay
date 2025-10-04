#!/bin/bash

# Initialize Postfix
mkdir -p /var/spool/postfix/pid
/usr/sbin/postfix start

echo "Starting Uvicorn server..."
# Jalankan aplikasi FastAPI dengan Uvicorn
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1