#!/usr/bin/env python3
import curses
import os
import json
import requests

API_BASE_URL = "http://localhost:8000/api"

def check_api_status():
    try:
        requests.get(API_BASE_URL + "/status", timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False

# --- Fungsi-fungsi yang memanggil API ---
def api_get(endpoint):
    try:
        res = requests.get(f"{API_BASE_URL}/{endpoint}")
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"Error API: {e}")
        return None

def api_post(endpoint, data):
    try:
        res = requests.post(f"{API_BASE_URL}/{endpoint}", json=data)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"Error API: {e.response.text if e.response else e}")
        return None

# --- Fungsi Menu ---
def draw_menu(stdscr, selected_row_idx, options, title="Menu"):
    stdscr.clear(); h, w = stdscr.getmaxyx()
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

def configure_sasl_cli():
    curses.endwin()
    print("\n--- Konfigurasi SASL ---")
    relay_host = input("Enter relay host (e.g. smtp.example.com:587): ")
    username = input("Enter SMTP username: ")
    password = input("Enter SMTP password: ")
    payload = {"relay_host": relay_host, "username": username, "password": password}
    result = api_post("configure_sasl", payload)
    if result: print(f"\n✅ Sukses: {result.get('message', 'OK')}")
    input("\nTekan Enter untuk kembali...")

def edit_sender_menu(stdscr):
    options = ["Add Sender", "Edit Sender", "Delete Sender", "View Senders", "Back"]
    current_row = 0
    while True:
        draw_menu(stdscr, current_row, options, "Edit Sender Menu")
        key = stdscr.getch()
        # ... (Navigasi menu seperti biasa)
        # Implementasi add/edit/delete dengan memanggil api_post, api_put, api_delete
        # Contoh untuk View Senders:
        if key in [curses.KEY_ENTER, 10, 13] and current_row == 3:
            curses.endwin()
            senders = api_get("senders")
            if senders is not None:
                print("\n--- Daftar Senders ---")
                if not senders: print("Tidak ada sender.")
                else:
                    for i, s in enumerate(senders): print(f"{i+1}. {s['name']} <{s['email']}>")
            input("\nTekan Enter untuk kembali...")
        elif key in [curses.KEY_ENTER, 10, 13] and current_row == 4:
            return

def check_mail_log_cli():
    curses.endwin()
    print("\n--- Cek Mail Log (50 baris terakhir) ---")
    data = api_get("mail_log?lines=50")
    if data and 'log' in data:
        print(data['log'])
    input("\nTekan Enter untuk kembali...")

def run_installation_wizard_cli():
    """Menjalankan wizard instalasi SMTP relay."""
    curses.endwin()
    print("\n--- Installation Wizard ---")
    
    # Get system info
    system_info = api_get("installation/system-info")
    if system_info:
        print(f"OS: {system_info.get('os_info', {}).get('name', 'Unknown')} {system_info.get('os_info', {}).get('version', '')}")
        print(f"Package Manager: {system_info.get('package_manager', 'Unknown')}")
        print(f"Sudo Access: {'Yes' if system_info.get('has_sudo', False) else 'No'}")
    else:
        print("❌ Could not get system information")
        input("\nTekan Enter untuk kembali ke menu...")
        return

    # Get available providers
    providers_data = api_get("installation/providers")
    if not providers_data:
        print("❌ Could not get provider information")
        input("\nTekan Enter untuk kembali ke menu...")
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
    
    result = api_post("installation/start", payload)
    if result and result.get('success'):
        print(f"\n✅ {result.get('message', 'Installation completed successfully!')}")
    else:
        error_msg = result.get('message', 'Installation failed') if result else 'Installation failed'
        print(f"\n❌ {error_msg}")

    input("\nTekan Enter untuk kembali ke menu...")

def run_uninstallation_cli():
    """Menjalankan proses uninstallasi."""
    curses.endwin()
    print("\n--- Uninstall SMTP Relay ---")
    print("This will remove SMTP relay configuration and restore system to original state.")
    
    confirm = input("Are you sure you want to uninstall? This cannot be undone. (type 'YES' to confirm): ").strip()
    if confirm != 'YES':
        print("Uninstall canceled.")
        input("\nTekan Enter untuk kembali ke menu...")
        return

    payload = {"confirm": True}
    result = api_post("installation/uninstall", payload)
    if result and result.get('success'):
        print(f"\n✅ {result.get('message', 'Uninstallation completed successfully!')}")
    else:
        error_msg = result.get('message', 'Uninstallation failed') if result else 'Uninstallation failed'
        print(f"\n❌ {error_msg}")

    input("\nTekan Enter untuk kembali ke menu...")

def check_installation_status_cli():
    """Memeriksa status instalasi SMTP relay."""
    curses.endwin()
    print("\n--- Installation Status ---")
    
    result = api_get("installation/status")
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

# --- Main Function ---
def main(stdscr):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    
    if not check_api_status():
        stdscr.addstr(1, 1, "Error: Tidak dapat terhubung ke server API di localhost:8000.")
        stdscr.addstr(2, 1, "Pastikan server utama (main.py) sudah berjalan.")
        stdscr.addstr(4, 1, "Tekan tombol apa saja untuk keluar.")
        stdscr.getch()
        return

    menu = [
        "Configure SASL", 
        "Edit Sender", 
        "Check Mail Log", 
        "Install SMTP Relay",
        "Uninstall SMTP Relay",
        "Check Installation Status",
        "Exit"
    ]
    current_row = 0
    while True:
        draw_menu(stdscr, current_row, menu, "SMTP Relay CLI")
        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0: current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1: current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row == 0: configure_sasl_cli()
            elif current_row == 1: edit_sender_menu(stdscr) # Anda bisa melengkapi logika edit/delete di sini
            elif current_row == 2: check_mail_log_cli()
            elif current_row == 3: run_installation_wizard_cli()
            elif current_row == 4: run_uninstallation_cli()
            elif current_row == 5: check_installation_status_cli()
            elif current_row == 6: break

if __name__ == "__main__":
    curses.wrapper(main)
