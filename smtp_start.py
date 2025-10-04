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

    menu = ["Configure SASL", "Edit Sender", "Check Mail Log", "Exit"]
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
            elif current_row == 3: break

if __name__ == "__main__":
    curses.wrapper(main)
