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

def run_installation_wizard_cli(stdscr):
    """Menjalankan wizard instalasi SMTP relay."""
    curses.endwin()
    print("\n--- Installation Wizard ---")
    
    # Get system info
    system_info = api_request("GET", "installation/system-info")
    if system_info:
        print(f"OS: {system_info.get('os_info', {}).get('name', 'Unknown')} {system_info.get('os_info', {}).get('version', '')}")
        print(f"Package Manager: {system_info.get('package_manager', 'Unknown')}")
        print(f"Sudo Access: {'Yes' if system_info.get('has_sudo', False) else 'No'}")
    else:
        print("❌ Could not get system information")
        input("\nTekan Enter untuk kembali ke menu...")
        curses.doupdate()
        return

    # Get available providers
    providers_data = api_request("GET", "installation/providers")
    if not providers_data:
        print("❌ Could not get provider information")
        input("\nTekan Enter untuk kembali ke menu...")
        curses.doupdate()
        return

    providers = providers_data.get('providers', [])
    print("\nAvailable providers:")
    for i, provider in enumerate(providers):
        print(f"  {i+1}. {provider['name']} - {provider['description']}")

    # Choose provider
    while True:
        try:
            choice = input(f"\nSelect provider (1-{len(providers)}): ").strip()
            if choice.isdigit():
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(providers):
                    selected_provider = providers[choice_idx]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(providers)}")
            else:
                print("Please enter a number")
        except (KeyboardInterrupt, EOFError):
            print("\nOperasi dibatalkan.")
            input("\nTekan Enter untuk kembali ke menu...")
            curses.doupdate()
            return

    print(f"\nSelected: {selected_provider['name']}")
    
    # Get credentials
    if selected_provider['name'].lower() == 'gmail':
        print("Note: For Gmail, use an App Password, not your regular password")
        print("Learn more: https://support.google.com/accounts/answer/185833")

    username = input("Enter your email/username: ").strip()
    password = input("Enter your password/App Password: ").strip()
    
    # For custom provider, also get host and port
    if selected_provider['name'].lower() == 'custom':
        relay_host = input("Enter SMTP server host: ").strip()
        while True:
            relay_port_str = input("Enter SMTP server port (default 587): ").strip() or "587"
            try:
                relay_port = int(relay_port_str)
                if 1 <= relay_port <= 65535:
                    break
                else:
                    print("Port must be between 1 and 65535")
            except ValueError:
                print("Please enter a valid number")
    else:
        # Use default settings for known providers
        if selected_provider['name'].lower() == 'gmail':
            relay_host = "smtp.gmail.com"
            relay_port = 587
        elif selected_provider['name'].lower() == 'outlook':
            relay_host = "smtp-mail.outlook.com"
            relay_port = 587
        elif selected_provider['name'].lower() == 'sendgrid':
            relay_host = "smtp.sendgrid.net"
            relay_port = 587
        elif selected_provider['name'].lower() == 'aws ses':
            relay_host = "email-smtp.us-east-1.amazonaws.com"  # Default region
            relay_port = 587
        else:
            # Fallback to basic defaults
            relay_host = "smtp.example.com"
            relay_port = 587

    # Confirm settings
    print(f"\nSummary:")
    print(f"  Provider: {selected_provider['name']}")
    print(f"  Server: {relay_host}:{relay_port}")
    print(f"  Username: {username}")
    
    confirm = input(f"\nProceed with installation? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Installation canceled.")
        input("\nTekan Enter untuk kembali ke menu...")
        curses.doupdate()
        return

    # Start installation
    print("\nStarting installation...")
    payload = {
        "config": {
            "relay_host": relay_host,
            "relay_port": relay_port,
            "username": username,
            "password": password,
            "provider": selected_provider['name'].lower().replace(' ', '_')
        }
    }
    
    result = api_request("POST", "installation/start", payload)
    if result and result.get('success'):
        print(f"\n✅ {result.get('message', 'Installation completed successfully!')}")
    else:
        error_msg = result.get('message', 'Installation failed') if result else 'Installation failed'
        print(f"\n❌ {error_msg}")

    input("\nTekan Enter untuk kembali ke menu...")
    curses.doupdate()

def run_uninstallation_cli(stdscr):
    """Menjalankan proses uninstallasi."""
    curses.endwin()
    print("\n--- Uninstall SMTP Relay ---")
    print("This will remove SMTP relay configuration and restore system to original state.")
    
    confirm = input("Are you sure you want to uninstall? This cannot be undone. (type 'YES' to confirm): ").strip()
    if confirm != 'YES':
        print("Uninstall canceled.")
        input("\nTekan Enter untuk kembali ke menu...")
        curses.doupdate()
        return

    payload = {"confirm": True}
    result = api_request("POST", "installation/uninstall", payload)
    if result and result.get('success'):
        print(f"\n✅ {result.get('message', 'Uninstallation completed successfully!')}")
    else:
        error_msg = result.get('message', 'Uninstallation failed') if result else 'Uninstallation failed'
        print(f"\n❌ {error_msg}")

    input("\nTekan Enter untuk kembali ke menu...")
    curses.doupdate()

def check_installation_status_cli(stdscr):
    """Memeriksa status instalasi SMTP relay."""
    curses.endwin()
    print("\n--- Installation Status ---")
    
    result = api_request("GET", "installation/status")
    if result:
        # Display system info
        os_info = result.get('system_info', {}).get('os_info', {})
        print(f"OS: {os_info.get('name', 'Unknown')} {os_info.get('version', '')}")
        print(f"Package Manager: {result.get('system_info', {}).get('package_manager', 'Unknown')}")
        print(f"Sudo Access: {'Yes' if result.get('system_info', {}).get('has_sudo', False) else 'No'}")
        
        # Display Postfix status
        postfix_status = result.get('system_info', {}).get('postfix_status', {})
        print(f"\nPostfix Status:")
        print(f"  Installed: {'Yes' if postfix_status.get('installed', False) else 'No'}")
        print(f"  Running: {'Yes' if postfix_status.get('running', False) else 'No'}")
        print(f"  Enabled: {'Yes' if postfix_status.get('enabled', False) else 'No'}")
        
        # Display verification results
        verification = result.get('verification_results', {})
        print(f"\nVerification Results:")
        print(f"  Postfix Running: {'Yes' if verification.get('postfix_running', False) else 'No'}")
        print(f"  Postfix Config Valid: {'Yes' if verification.get('config_valid', False) else 'No'}")
        print(f"  SASL Configured: {'Yes' if verification.get('sasl_configured', False) else 'No'}")
        print(f"  All Checks Passed: {'Yes' if verification.get('all_checks_passed', False) else 'No'}")
    else:
        print("❌ Could not get installation status")
    
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
        "Install SMTP Relay",
        "Uninstall SMTP Relay",
        "Check Installation Status",
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
                run_installation_wizard_cli(stdscr)
            elif current_row == 7:
                run_uninstallation_cli(stdscr)
            elif current_row == 8:
                check_installation_status_cli(stdscr)
            elif current_row == 9:
                break # Keluar dari loop

if __name__ == "__main__":
    # Gunakan curses.wrapper untuk menangani setup dan teardown layar dengan aman
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Terjadi error: {e}")

