#!/usr/bin/env python3
import curses
import subprocess
import os
import sys

def draw_menu(stdscr, selected_row_idx, options, title="Menu"):
    stdscr.clear()
    stdscr.addstr(0, 0, f"{title}\n", curses.A_BOLD)

    for idx, row in enumerate(options):
        x = 2
        y = idx + 2
        if idx == selected_row_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, f"{idx+1}. {row}")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, f"{idx+1}. {row}")

    stdscr.refresh()

def show_welcome_screen(stdscr):
    """Display welcome screen with project information"""
    stdscr.clear()
    
    # Welcome message
    welcome_text = [
        "╔══════════════════════════════════════════════════════════════════════════════╗",
        "║                           SMTP Relay Setup Tool                              ║",
        "║                                                                              ║",
        "║                    The Ultimate Postfix Configuration Tool                   ║",
        "╚══════════════════════════════════════════════════════════════════════════════╝",
        "",
        "This tool helps you set up and manage SMTP relays with Postfix.",
        "Choose your preferred interface mode below:",
        ""
    ]
    
    for i, line in enumerate(welcome_text):
        stdscr.addstr(i + 1, 2, line)
    
    stdscr.refresh()

def main(stdscr):
    # Set up curses
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    
    # Show welcome screen briefly
    show_welcome_screen(stdscr)
    stdscr.addstr(len(["╔══════════════════════════════════════════════════════════════════════════════╗",
        "║                           SMTP Relay Setup Tool                              ║",
        "║                                                                              ║",
        "║                    The Ultimate Postfix Configuration Tool                   ║",
        "╚══════════════════════════════════════════════════════════════════════════════╝",
        "",
        "This tool helps you set up and manage SMTP relays with Postfix.",
        "Choose your preferred interface mode below:",
        ""]) + 1, 2, "Press any key to continue...")
    stdscr.refresh()
    stdscr.getch()
    
    # Main menu options
    menu = [
        "Run in Terminal UI Mode (TUI)",
        "Run in Web UI Mode",
        "Start API Server (for development)",
        "Exit"
    ]
    
    current_row = 0

    while True:
        draw_menu(stdscr, current_row, menu, "SMTP Relay Setup - Choose Interface Mode")
        
        # Add helpful information at bottom
        stdscr.addstr(len(menu) + 3, 2, "↑↓ to navigate, Enter to select")
        stdscr.addstr(len(menu) + 4, 2, "TUI: Interactive terminal interface with menus and options")
        stdscr.addstr(len(menu) + 5, 2, "Web UI: Browser-based interface for relay management")
        stdscr.addstr(len(menu) + 6, 2, "API: Run the backend API server separately")
        
        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row == 0:  # Terminal UI Mode
                # Run the TUI version
                stdscr.clear()
                stdscr.addstr(2, 2, "Starting Terminal UI Mode...")
                stdscr.addstr(4, 2, "Press any key to continue...")
                stdscr.refresh()
                stdscr.getch()
                
                # Close curses and run the TUI program
                curses.endwin()
                os.execv(sys.executable, [sys.executable, 'smtp_start.py'])
                
            elif current_row == 1:  # Web UI Mode
                stdscr.clear()
                stdscr.addstr(2, 2, "Starting Web UI Mode...")
                stdscr.addstr(4, 2, "Web UI will be available at http://localhost:5000")
                stdscr.addstr(5, 2, "Make sure the API server is running on port 5001")
                stdscr.addstr(6, 2, "Press any key to continue...")
                stdscr.refresh()
                stdscr.getch()
                
                # Close curses and run the web UI
                curses.endwin()
                os.execv(sys.executable, [sys.executable, 'web_ui.py'])
                
            elif current_row == 2:  # API Server Mode
                stdscr.clear()
                stdscr.addstr(2, 2, "Starting API Server on port 5001...")
                stdscr.addstr(4, 2, "API will be available at http://localhost:5001")
                stdscr.addstr(5, 2, "Press any key to continue...")
                stdscr.refresh()
                stdscr.getch()
                
                # Close curses and run the API server
                curses.endwin()
                os.execv(sys.executable, [sys.executable, 'api_server.py'])
                
            elif current_row == 3:  # Exit
                break

if __name__ == "__main__":
    curses.wrapper(main)