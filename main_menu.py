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
        "Run mode TUI/CLI + server",
        "Web UI + server mode",
        "Exit"
    ]
    current_row = 0

    while True:
        draw_menu(stdscr, current_row, menu, "SMTP Relay Control Panel")
        stdscr.addstr(len(menu) + 2, 2, "Select mode to run the application.")
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0: current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1: current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            curses.endwin()
            if current_row == 0:  # Run mode TUI/CLI + server
                import time
                # Check if uvicorn is available
                result = subprocess.run(["which", "uvicorn"], capture_output=True, text=True)
                if result.returncode != 0:
                    print("Error: uvicorn tidak ditemukan. Pastikan telah diinstal dengan 'pip install uvicorn'.")
                    input("Tekan Enter untuk kembali ke menu...")
                    break
                print("--- Starting server and CLI mode ---")
                print("Tekan CTRL+C untuk berhenti.")
                
                # Remove any existing port file
                port_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".server_port")
                if os.path.exists(port_file):
                    os.remove(port_file)
                
                # Start the server in background
                server_process = subprocess.Popen(["python3", "run_server.py"])
                
                # Wait a bit for the server to start and write the port file
                max_wait_time = 10  # Wait up to 10 seconds
                waited = 0
                while waited < max_wait_time and not os.path.exists(port_file):
                    time.sleep(0.5)
                    waited += 0.5
                
                if not os.path.exists(port_file):
                    print("Error: Server tidak bisa memulai dengan benar.")
                    server_process.terminate()
                    server_process.wait()
                    input("Tekan Enter untuk kembali...")
                    break
                
                print("Menunggu server siap menerima permintaan API...")
                # Give the server additional time to be fully ready to accept requests
                time.sleep(3)
                
                try:
                    subprocess.run(["python3", "smtp_start.py"])
                finally:
                    # Terminate the server when CLI mode exits
                    server_process.terminate()
                    server_process.wait()
                    # Clean up the port file
                    if os.path.exists(port_file):
                        os.remove(port_file)
                break
            elif current_row == 1:  # Web UI + server mode
                # Check if uvicorn is available
                result = subprocess.run(["which", "uvicorn"], capture_output=True, text=True)
                if result.returncode != 0:
                    print("Error: uvicorn tidak ditemukan. Pastikan telah diinstal dengan 'pip install uvicorn'.")
                    input("Tekan Enter untuk kembali ke menu...")
                    break
                print("--- Starting Web UI server ---")
                print("Tekan CTRL+C untuk berhenti.")
                # Use our new run_server.py script that automatically finds an available port
                subprocess.run(["python3", "run_server.py"])
                break
            elif current_row == 2:  # Exit
                break

if __name__ == "__main__":
    curses.wrapper(main)
