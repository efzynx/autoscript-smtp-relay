#!/bin/bash
set -e # Hentikan skrip jika ada perintah yang gagal

POSTFIX_CONFIG_DIR="/etc/postfix"
POSTFIX_BACKUP_DIR="/etc/postfix.bak"

# Jika volume konfigurasi kosong (menandakan kali pertama dijalankan),
# isi dengan menyalin dari cadangan yang kita buat di Dockerfile.
if [ ! -f "$POSTFIX_CONFIG_DIR/main.cf" ]; then
    echo "Volume konfigurasi Postfix kosong. Menyalin dari cadangan default..."
    # Opsi -a akan menyalin semua file beserta izinnya
    cp -a $POSTFIX_BACKUP_DIR/* $POSTFIX_CONFIG_DIR/
    echo "Konfigurasi default berhasil disalin."
fi

# Jalankan newaliases untuk memastikan database alias ada dan terbaru
echo "Memastikan database alias..."
newaliases

# Jalankan layanan Postfix menggunakan perintah langsung
echo "Menjalankan layanan Postfix..."
/usr/sbin/postfix start

# Tunggu sampai Postfix siap
echo "Menunggu Postfix siap..."
TIMEOUT=20
COUNT=0
while [ ! -S /var/spool/postfix/public/pickup ]; do
  if [ "$COUNT" -ge "$TIMEOUT" ]; then
    echo "ERROR: Postfix gagal siap dalam ${TIMEOUT} detik."
    exit 1
  fi
  sleep 1
  ((COUNT++))
  echo -n "."
done
echo
echo "Layanan Postfix siap dalam ${COUNT} detik."

# Jalankan aplikasi utama
echo "Menjalankan server Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1