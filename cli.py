#!/usr/bin/env python3
"""
CLI untuk berinteraksi dengan SMTP Relay API.
"""
import requests
import curses
import os
import json

# URL dapat di-override dengan environment variable, jika tidak, gunakan default.
API_BASE_URL = os.environ.get("API_URL", "http://localhost:8000/api")

# --- Fungsi-fungsi pembantu untuk berkomunikasi dengan API ---

def check_api_status():
    """Memeriksa apakah server API berjalan sebelum memulai CLI."""
    try:
        requests.get(f"{API_BASE_URL}/status", timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False

def api_request(method, endpoint, data=None):
    """Fungsi terpusat untuk semua permintaan API."""
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        if method.upper() == 'GET':
            response = requests.get(url)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(url)
        else:
            print(f"Metode HTTP tidak dikenal: {method}")
            return None
        
        response.raise_for_status() # Akan melempar error jika status code 4xx atau 5xx
        # Beberapa respons (seperti DELETE) mungkin tidak memiliki body JSON
        return response.json() if response.text else {"status": "success"}
    except requests.exceptions.HTTPError as e:
        # Mencoba mengambil detail error dari respons JSON
        try:
            error_details = e.response.json().get('detail', e.response.text)
        except json.JSONDecodeError:
            error_details = e.response.text
        print(f"\n❌ Error API: {e.response.status_code} - {error_details}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error Koneksi: Tidak dapat terhubung ke server API.\n   {e}")
        return None

# --- Fungsi-fungsi yang dipanggil oleh menu ---

def configure_sasl_cli(stdscr):
    """Menampilkan form untuk konfigurasi SASL."""
    curses.endwin()
    print("\n--- Konfigurasi SASL (SMTP Relay) ---")
    try:
        relay_host = input("Enter relay host (contoh: smtp.example.com): ")
        relay_port = input("Enter port (contoh: 587): ")
        username = input("Enter SMTP username: ")
        password = input("Enter SMTP password: ")
        
        payload = {
            "relay_host": relay_host,
            "relay_port": int(relay_port),
            "username": username,
            "password": password
        }
        result = api_request("POST", "configure_sasl", payload)
        if result: 
            print(f"\n✅ Sukses: {result.get('message', 'Konfigurasi berhasil disimpan.')}")
    except ValueError:
        print("\n❌ Error: Port harus berupa angka.")
    except (KeyboardInterrupt, EOFError):
        print("\nOperasi dibatalkan.")
    input("\nTekan Enter untuk kembali ke menu...")
    curses.doupdate() # Mengembalikan layar curses

def view_senders_cli(stdscr):
    """Menampilkan daftar sender dari API."""
    curses.endwin()
    print("\n--- Daftar Sender ---")
    senders = api_request("GET", "senders")
    if senders is not None:
        if not senders:
            print("Belum ada sender yang dikonfigurasi.")
        else:
            for i, sender in enumerate(senders):
                print(f"{i+1}. {sender['name']} <{sender['email']}>")
    input("\nTekan Enter untuk kembali ke menu...")
    curses.doupdate()

def add_sender_cli(stdscr):
    """Menampilkan form untuk menambah sender baru."""
    curses.endwin()
    print("\n--- Tambah Sender Baru ---")
    try:
        name = input("Masukkan nama sender: ")
        email = input("Masukkan email sender: ")
        if name and email:
            payload = {"name": name, "email": email}
            result = api_request("POST", "senders", payload)
            if result:
                print("\n✅ Sender berhasil ditambahkan!")
        else:
            print("\nNama dan email tidak boleh kosong.")
    except (KeyboardInterrupt, EOFError):
        print("\nOperasi dibatalkan.")
    input("\nTekan Enter untuk kembali ke menu...")
    curses.doupdate()
    
def check_mail_log_cli(stdscr):
    """Menampilkan 50 baris terakhir dari log email."""
    curses.endwin()
    print("\n--- Log Email (50 baris terakhir) ---")
    data = api_request("GET", "mail_log?lines=50")
    if data and 'log' in data:
        print(data['log'])
    else:
        print("Gagal mengambil log atau log tidak ditemukan.")
    input("\nTekan Enter untuk kembali ke menu...")
    curses.doupdate()

def check_queue_cli(stdscr):
    """Menampilkan status antrean email."""
    curses.endwin()
    print("\n--- Antrean Email (Mail Queue) ---")
    data = api_request("GET", "mail_queue")
    if data and 'queue' in data:
        print(data['queue'])
    input("\nTekan Enter untuk kembali ke menu...")
    curses.doupdate()

def flush_queue_cli(stdscr):
    """Mengirim perintah flush antrean email."""
    curses.endwin()
    print("\n--- Flush Mail Queue ---")
    confirm = input("Apakah Anda yakin ingin melakukan flush? (y/n): ").lower()
    if confirm == 'y':
        result = api_request("POST", "flush_queue")
        if result:
            print(f"\n✅ Sukses: {result.get('message', 'Perintah flush terkirim.')}")
    else:
        print("Flush dibatalkan.")
    input("\nTekan Enter untuk kembali ke menu...")
    curses.doupdate()

# --- Fungsi dasar untuk menggambar menu ---
def draw_menu(stdscr, selected_row_idx, options, title="Menu"):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(0, 0, f"{title}\n", curses.A_BOLD)
    for idx, row in enumerate(options):
        x, y = 2, idx + 2
        if idx == selected_row_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, f"{idx+1}. {row}")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, f"{idx+1}. {row}")
    stdscr.refresh()

# --- Fungsi utama yang menjalankan aplikasi CLI ---
def main(stdscr):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    
    if not check_api_status():
        stdscr.clear()
        stdscr.addstr(1, 1, "❌ Error: Tidak dapat terhubung ke server API di localhost:8000.")
        stdscr.addstr(2, 1, "   Pastikan server utama (main.py atau Docker) sudah berjalan.")
        stdscr.addstr(4, 1, "Tekan tombol apa saja untuk keluar.")
        stdscr.getch()
        return

    menu_options = [
        "Konfigurasi SASL (SMTP Relay)",
        "Lihat Daftar Sender",
        "Tambah Sender Baru",
        "Lihat Log Email",
        "Lihat Antrean Email",
        "Flush Antrean Email",
        "Keluar"
    ]
    current_row = 0

    while True:
        draw_menu(stdscr, current_row, menu_options, "SMTP Relay CLI")
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row == 0:
                configure_sasl_cli(stdscr)
            elif current_row == 1:
                view_senders_cli(stdscr)
            elif current_row == 2:
                add_sender_cli(stdscr)
            elif current_row == 3:
                check_mail_log_cli(stdscr)
            elif current_row == 4:
                check_queue_cli(stdscr)
            elif current_row == 5:
                flush_queue_cli(stdscr)
            elif current_row == 6:
                break # Keluar dari loop

if __name__ == "__main__":
    # Gunakan curses.wrapper untuk menangani setup dan teardown layar dengan aman
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Terjadi error: {e}")

