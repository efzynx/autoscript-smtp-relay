#!/usr/bin/env python3
import curses
import subprocess
import os
import json

menu = [
    "Install Postfix",
    "Configure SASL (sasl_passwd)",
    "Edit Sender (sender.json)",
    "Send Test Email",
    "Check Mail Log",
    "Exit"
]

SENDER_FILE = "sender.json"

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

def install_postfix():
    subprocess.run(["sudo", "apt-get", "install", "-y", "postfix"], check=False)

def configure_sasl():
    relay_host = input("Enter relay host (e.g. smtp-relay.brevo.com:587): ")
    user = input("Enter SMTP username: ")
    passwd = input("Enter SMTP password: ")

    with open("/etc/postfix/sasl_passwd", "w") as f:
        f.write(f"[{relay_host}] {user}:{passwd}\n")

    os.system("sudo postmap /etc/postfix/sasl_passwd")
    os.system("sudo chmod 600 /etc/postfix/sasl_passwd*")
    os.system("sudo systemctl restart postfix")
    print("SASL configured successfully.")

def load_senders():
    if not os.path.exists(SENDER_FILE):
        with open(SENDER_FILE, "w") as f:
            json.dump([], f)
        return []
    with open(SENDER_FILE, "r") as f:
        return json.load(f)

def save_senders(senders):
    with open(SENDER_FILE, "w") as f:
        json.dump(senders, f, indent=2)

def edit_sender_menu(stdscr):
    senders = load_senders()
    options = ["Add Sender", "Edit Sender", "Delete Sender", "View Senders", "Back"]

    current_row = 0
    while True:
        draw_menu(stdscr, current_row, options, "Edit Sender Menu")
        stdscr.addstr(len(options) + 3, 2, "Use ↑↓ to navigate, Enter to select.")
        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row == 4:  # Back
                return

            if current_row == 0:  # Add
                curses.endwin()
                name = input("Enter sender name: ")
                email = input("Enter sender email: ")
                senders.append({"name": name, "email": email})
                save_senders(senders)
                print("✅ Sender added.")
                input("Press Enter to return...")

            elif current_row == 1:  # Edit
                curses.endwin()
                if not senders:
                    print("No senders to edit.")
                else:
                    for i, s in enumerate(senders):
                        print(f"{i+1}. {s['name']} <{s['email']}>")
                    idx = int(input("Select sender number to edit: ")) - 1
                    if 0 <= idx < len(senders):
                        senders[idx]["name"] = input(f"New name ({senders[idx]['name']}): ") or senders[idx]["name"]
                        senders[idx]["email"] = input(f"New email ({senders[idx]['email']}): ") or senders[idx]["email"]
                        save_senders(senders)
                        print("✅ Sender updated.")
                input("Press Enter to return...")

            elif current_row == 2:  # Delete
                curses.endwin()
                if not senders:
                    print("No senders to delete.")
                else:
                    for i, s in enumerate(senders):
                        print(f"{i+1}. {s['name']} <{s['email']}>")
                    idx = int(input("Select sender number to delete: ")) - 1
                    if 0 <= idx < len(senders):
                        del senders[idx]
                        save_senders(senders)
                        print("🗑️ Sender deleted.")
                input("Press Enter to return...")

            elif current_row == 3:  # View
                try:
                    stdscr.clear()
                    stdscr.addstr(0, 0, "📜 List of Senders:\n", curses.A_BOLD)
                    if not senders:
                        stdscr.addstr(2, 2, "No senders available.")
                    else:
                        for i, s in enumerate(senders):
                            stdscr.addstr(i+2, 2, f"{i+1}. {s['name']} <{s['email']}>")
                    stdscr.addstr(curses.LINES-2, 0, "Press any key to return...")
                    stdscr.refresh()
                    stdscr.getch()
                except Exception:
                    curses.endwin()
                    print("\n📜 List of senders:")
                    if not senders:
                        print("No senders available.")
                    else:
                        for i, s in enumerate(senders):
                            print(f"{i+1}. {s['name']} <{s['email']}>")
                    input("Press Enter to return...")
                    
            stdscr.clear()
            curses.doupdate()

def select_sender(stdscr):
    senders = load_senders()
    if not senders:
        print("No senders found. Please add via 'Edit Sender' menu first.")
        return None, None

    options = [f"{s['name']} <{s['email']}>" for s in senders]
    current_row = 0
    while True:
        draw_menu(stdscr, current_row, options, "Select Sender")
        stdscr.addstr(len(options) + 3, 2, "Use ↑↓ to choose sender, Enter to confirm.")
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            return senders[current_row]["email"], senders[current_row]["name"]

def send_test_email(stdscr):
    sender_email, sender_name = select_sender(stdscr)
    if not sender_email:
        return

    curses.endwin()
    print(f"\nSelected sender: {sender_name} <{sender_email}>\n")
    to = input("Enter recipient email: ")
    subject = input("Enter subject: ")
    body = input("Enter message: ")

    mail_cmd = f'echo "{body}" | mail -a "From: {sender_name} <{sender_email}>" -s "{subject}" {to}'
    subprocess.run(mail_cmd, shell=True)
    print("✅ Test email sent.\n")
    input("Press Enter to return...")

def check_mail_log():
    log_paths = ["/var/log/mail.log", "/var/log/maillog"]
    log_file = next((p for p in log_paths if os.path.exists(p)), None)

    if not log_file:
        print("❌ Tidak ditemukan mail log di sistem ini.")
        input("Press Enter to return...")
        return

    print(f"\n📜 Showing last 30 lines of {log_file}:\n")
    os.system(f"sudo tail -n 30 {log_file}")
    print("\n✅ Done.\n")
    input("Press Enter to return...")

def main(stdscr):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    current_row = 0

    while True:
        draw_menu(stdscr, current_row, menu, "SMTP Relay Setup (Postfix + SASL)")
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            stdscr.clear()
            stdscr.refresh()

            if current_row == 0:
                install_postfix()
            elif current_row == 1:
                configure_sasl()
            elif current_row == 2:
                edit_sender_menu(stdscr)
            elif current_row == 3:
                send_test_email(stdscr)
            elif current_row == 4:
                check_mail_log()
            elif current_row == 5:
                break

            stdscr.addstr(5, 0, "Press any key to return to menu...")
            stdscr.getch()

curses.wrapper(main)
