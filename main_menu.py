#!/usr/bin/env python3
import os
import subprocess
import curses

def draw_menu(stdscr, selected_row_idx, options, title="Menu"):
    stdscr.clear()
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

def main(stdscr):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    
    menu = [
        "Jalankan Server (Web UI & API)",
        "Jalankan Mode CLI (Terminal)",
        "Keluar"
    ]
    current_row = 0

    while True:
        draw_menu(stdscr, current_row, menu, "SMTP Relay Control Panel")
        stdscr.addstr(len(menu) + 2, 2, "Pilih mode untuk menjalankan aplikasi.")
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0: current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1: current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            curses.endwin()
            if current_row == 0:
                print("--- Menjalankan Server Utama (Uvicorn) di http://localhost:8000 ---")
                print("Tekan CTRL+C untuk berhenti.")
                subprocess.run(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"])
                break
            elif current_row == 1:
                print("--- Membuka Mode CLI ---")
                subprocess.run(["python3", "smtp_start.py"])
                break
            elif current_row == 2:
                break

if __name__ == "__main__":
    curses.wrapper(main)
