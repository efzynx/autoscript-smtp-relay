#!/usr/bin/env python3
"""
Aplikasi Utama SMTP Relay - Menggabungkan API dan Web UI
Dijalankan dengan Uvicorn untuk performa tinggi.
"""
import json
import subprocess
import os
import base64
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Inisialisasi Aplikasi FastAPI ---
app = FastAPI(
    title="SMTP Relay API & UI",
    description="Layanan terpadu untuk mengelola Postfix SMTP Relay."
)

# --- Path Absolut ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SENDER_FILE = os.path.join(BASE_DIR, "sender.json")
TEMPLATE_FILE = os.path.join(BASE_DIR, "templates", "index.html")

# --- Model Data (untuk validasi request body) ---
class Sender(BaseModel):
    name: str
    email: str

class TestEmail(BaseModel):
    from_email: str
    from_name: str
    to_email: str
    subject: str
    body: str

# --- Fungsi Helper ---
def load_senders():
    if not os.path.exists(SENDER_FILE):
        return []
    try:
        with open(SENDER_FILE, "r") as f:
            content = f.read()
            return json.loads(content) if content else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_senders(senders: list):
    try:
        with open(SENDER_FILE, "w") as f:
            json.dump(senders, f, indent=2)
    except Exception as e:
        logging.error(f"Gagal menyimpan senders: {e}")

def run_command(command: list):
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False, timeout=15)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logging.error(f"Command error: {e}")
        return None

# --- Endpoint API ---

@app.get("/api/status", tags=["Status"])
def get_status():
    """Mendapatkan status sistem saat ini."""
    senders = load_senders()
    queue_result = run_command(['sudo', 'postqueue', '-p'])
    queue_status = "Error"
    if queue_result:
        queue_status = queue_result.stdout.strip() or "Mail queue is empty"
        if "Mail system is down" in queue_result.stderr:
            queue_status = "Postfix not running properly"
    
    postfix_result = run_command(['sudo', 'postfix', 'status'])
    postfix_running = postfix_result.returncode == 0 if postfix_result else False

    return {'senders_count': len(senders), 'queue_status': queue_status, 'postfix_running': postfix_running}

@app.get("/api/senders", response_model=list[Sender], tags=["Senders"])
def get_senders():
    """Mengambil semua data sender."""
    return load_senders()

@app.post("/api/senders", status_code=201, tags=["Senders"])
def add_sender(sender: Sender):
    """Menambahkan sender baru."""
    senders = load_senders()
    senders.append(sender.dict())
    save_senders(senders)
    return {"status": "success", "message": "Sender berhasil ditambahkan."}

@app.put("/api/senders/{sender_id}", tags=["Senders"])
def update_sender(sender_id: int, sender: Sender):
    """Memperbarui sender yang ada."""
    senders = load_senders()
    if 0 <= sender_id < len(senders):
        senders[sender_id] = sender.dict()
        save_senders(senders)
        return {"status": "success", "message": "Sender berhasil diperbarui."}
    raise HTTPException(status_code=404, detail="Sender not found")

@app.delete("/api/senders/{sender_id}", tags=["Senders"])
def delete_sender(sender_id: int):
    """Menghapus sender."""
    senders = load_senders()
    if 0 <= sender_id < len(senders):
        del senders[sender_id]
        save_senders(senders)
        return {"status": "success", "message": "Sender berhasil dihapus."}
    raise HTTPException(status_code=404, detail="Sender not found")

@app.post("/api/send_test_email", tags=["Email"])
def send_test_email(email: TestEmail):
    """Mengirim email uji coba."""
    mail_cmd = f'echo "{email.body}" | mail -a "From: {email.from_name} <{email.from_email}>" -s "{email.subject}" {email.to_email}'
    result = run_command(['bash', '-c', mail_cmd])
    if result and result.returncode == 0:
        return {"status": "success", "message": "Test email sent successfully"}
    error_message = result.stderr if result else "Unknown error"
    raise HTTPException(status_code=500, detail=f"Failed to send email: {error_message}")

@app.get("/api/mail_queue", tags=["Queue"])
def get_mail_queue():
    result = run_command(['sudo', 'postqueue', '-p'])
    if result:
        return {"status": "success", "queue": result.stdout or "Mail queue is empty"}
    raise HTTPException(status_code=500, detail="Failed to get mail queue")

@app.post("/api/flush_queue", tags=["Queue"])
def flush_mail_queue():
    result = run_command(['sudo', 'postqueue', '-f'])
    if result and result.returncode == 0:
        return {"status": "success", "message": "Mail queue has been flushed"}
    raise HTTPException(status_code=500, detail="Failed to flush queue")

# --- Endpoint untuk Menyajikan Web UI ---
@app.get("/", include_in_schema=False)
async def read_index():
    """Menyajikan halaman utama web UI."""
    if not os.path.exists(TEMPLATE_FILE):
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(TEMPLATE_FILE)
