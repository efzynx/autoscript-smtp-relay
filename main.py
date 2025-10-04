#!/usr/bin/env python3
"""
Aplikasi Utama SMTP Relay - Menggabungkan API dan Web UI
Dijalankan dengan Uvicorn untuk performa tinggi.
"""
import json
import subprocess
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# --- Setup logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="SMTP Relay API & UI")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SENDER_FILE = os.path.join(BASE_DIR, "sender.json")
TEMPLATE_FILE = os.path.join(BASE_DIR, "templates", "index.html")

# --- Model Data ---
class Sender(BaseModel): name: str; email: str
class TestEmail(BaseModel): from_email: str; from_name: str; to_email: str; subject: str; body: str
class SaslConfig(BaseModel): relay_host: str; username: str; password: str

# --- Fungsi Helper ---
def load_senders():
    if not os.path.exists(SENDER_FILE): return []
    try:
        with open(SENDER_FILE, "r") as f:
            content = f.read()
            return json.loads(content) if content else []
    except (json.JSONDecodeError, FileNotFoundError): return []

def save_senders(senders: list):
    with open(SENDER_FILE, "w") as f: json.dump(senders, f, indent=2)

def run_command(command: list):
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False, timeout=15)
    except Exception as e:
        logging.error(f"Command error: {e}"); return None

# --- Endpoint API ---

@app.get("/api/status", tags=["Status"])
def get_status():
    senders = load_senders()
    queue_result = run_command(['sudo', 'postqueue', '-p'])
    queue_status = "Error"
    if queue_result:
        queue_status = queue_result.stdout.strip() or "Mail queue is empty"
        if "Mail system is down" in queue_result.stderr: queue_status = "Postfix not running properly"
    
    postfix_result = run_command(['sudo', 'postfix', 'status'])
    postfix_running = postfix_result.returncode == 0 if postfix_result else False

    return {'senders_count': len(senders), 'queue_status': queue_status, 'postfix_running': postfix_running}

@app.get("/api/senders", response_model=list[Sender], tags=["Senders"])
def get_senders(): return load_senders()

@app.post("/api/senders", status_code=201, tags=["Senders"])
def add_sender(sender: Sender):
    senders = load_senders(); senders.append(sender.dict()); save_senders(senders)
    return {"status": "success"}

@app.put("/api/senders/{sender_id}", tags=["Senders"])
def update_sender(sender_id: int, sender: Sender):
    senders = load_senders()
    if 0 <= sender_id < len(senders):
        senders[sender_id] = sender.dict(); save_senders(senders)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Sender not found")

@app.delete("/api/senders/{sender_id}", tags=["Senders"])
def delete_sender(sender_id: int):
    senders = load_senders()
    if 0 <= sender_id < len(senders):
        del senders[sender_id]; save_senders(senders)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Sender not found")

@app.post("/api/configure_sasl", tags=["Konfigurasi"])
def configure_sasl(config: SaslConfig):
    try:
        sasl_path = '/etc/postfix/sasl_passwd'
        with open(sasl_path, 'w') as f: f.write(f"[{config.relay_host}] {config.username}:{config.password}\n")
        run_command(['sudo', 'chmod', '600', sasl_path])
        
        postmap_result = run_command(['sudo', 'postmap', sasl_path])
        if postmap_result.returncode != 0: raise HTTPException(500, f"Gagal postmap: {postmap_result.stderr}")

        run_command(['sudo', 'postconf', '-e', f'relayhost = [{config.relay_host}]'])
        run_command(['sudo', 'postconf', '-e', 'smtp_use_tls = yes'])
        run_command(['sudo', 'postconf', '-e', 'smtp_sasl_auth_enable = yes'])
        run_command(['sudo', 'postconf', '-e', f'smtp_sasl_password_maps = hash:{sasl_path}'])
        run_command(['sudo', 'postconf', '-e', 'smtp_sasl_security_options = noanonymous'])

        reload_result = run_command(['sudo', 'postfix', 'reload'])
        if reload_result.returncode != 0: raise HTTPException(500, f"Gagal reload Postfix: {reload_result.stderr}")
            
        return {"status": "success", "message": "Konfigurasi SASL berhasil diterapkan."}
    except Exception as e:
        raise HTTPException(500, f"Error internal: {e}")

@app.get("/api/mail_log", tags=["Monitoring"])
def get_mail_log(lines: int = 50):
    log_path = "/var/log/mail.log"
    if not os.path.exists(log_path): log_path = "/var/log/maillog"
    if not os.path.exists(log_path): raise HTTPException(404, "Mail log not found")
    
    result = run_command(['sudo', 'tail', '-n', str(lines), log_path])
    if result and result.returncode == 0: return JSONResponse(content={"log": result.stdout})
    raise HTTPException(500, "Failed to read mail log")

@app.get("/api/mail_queue", tags=["Monitoring"])
def get_mail_queue():
    """Melihat antrean email."""
    result = run_command(['sudo', 'postqueue', '-p'])
    if result:
        return {"status": "success", "queue": result.stdout or "Mail queue is empty"}
    raise HTTPException(status_code=500, detail="Gagal mengambil data antrean email")

@app.post("/api/flush_queue", tags=["Monitoring"])
def flush_mail_queue():
    """Membersihkan (flush) antrean email."""
    result = run_command(['sudo', 'postqueue', '-f'])
    if result and result.returncode == 0:
        return {"status": "success", "message": "Antrean email berhasil di-flush"}
    raise HTTPException(status_code=500, detail=f"Gagal melakukan flush: {result.stderr if result else ''}")
# -----------------------------------------------

@app.post("/api/send_test_email", tags=["Email"])
def send_test_email(email: TestEmail):
    mail_cmd = f'echo "{email.body}" | mail -a "From: {email.from_name} <{email.from_email}>" -s "{email.subject}" {email.to_email}'
    result = run_command(['bash', '-c', mail_cmd])
    if result and result.returncode == 0: return {"status": "success"}
    raise HTTPException(500, f"Gagal kirim email: {result.stderr if result else 'Unknown error'}")

# --- Endpoint UI ---
@app.get("/", include_in_schema=False)
async def read_index():
    if not os.path.exists(TEMPLATE_FILE): raise HTTPException(404, "index.html not found")
    return FileResponse(TEMPLATE_FILE)
