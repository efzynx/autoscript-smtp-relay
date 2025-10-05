#!/bin/bash
set -e

echo "Menjalankan server Uvicorn..."
echo "Aplikasi ini sekarang akan mengontrol Postfix di sistem host Anda."

exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

