#!/usr/bin/env python3
import curses
import subprocess
import os
import json
import base64

menu = [
    "Install Postfix",
    "Configure SASL (sasl_passwd)",
    "Edit Sender (sender.json)",
    "Send Test Email",
    "Check Mail Log",
    "Mail Queue",
    "Uninstall/Reset",
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
    
    # Automatically configure main.cf with default settings
    main_cf_config = f"""
relayhost = [{relay_host}]:587
smtp_use_tls = yes
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_sasl_tls_security_options = noanonymous
"""
    
    # Write the configuration to main.cf
    os.system(f"echo '{main_cf_config}' | sudo tee -a /etc/postfix/main.cf > /dev/null")
    
    os.system("sudo systemctl restart postfix")
    print("SASL configured successfully with automatic main.cf configuration.")
    
    # Ask if user wants to run an automatic test
    auto_test = input("Do you want to run an automatic test after configuration? (y/n): ").strip().lower()
    if auto_test == 'y' or auto_test == 'yes':
        # Send a test email to a dummy address to check if relay works
        dummy_email = input("Enter a dummy email address to test relay (or press Enter to skip): ").strip()
        if dummy_email:
            send_test_email_to_address(dummy_email, f"Test subject - {relay_host} relay")
    
    # Save relay info in sender.json for this account
    save_relay_info_to_sender(relay_host, user, passwd)


def save_relay_info_to_sender(relay_host, username, password):
    """Save relay information to the sender.json file"""
    senders = load_senders()
    
    # If there are no senders yet, we can't add relay info to an existing sender
    # So we can either create a new sender with relay info or just save the relay
    # Let's create a new sender with relay info
    if not senders:
        print("\nNo existing senders found. Creating a new sender with relay info...")
        sender_name = input("Enter sender name for this relay: ")
        sender_email = input("Enter sender email for this relay: ")
        relay_entry = {
            "name": sender_name,
            "email": sender_email,
            "relay_host": relay_host,
            "username": username,
            "password": password
        }
        senders.append(relay_entry)
        save_senders(senders)
        print("✅ Relay information saved with sender details.")
    else:
        # If there are existing senders, allow user to pick one to add relay info to
        print("\nExisting senders:")
        for i, sender in enumerate(senders):
            print(f"{i+1}. {sender['name']} <{sender['email']}>")
        print(f"{len(senders)+1}. Create new sender with relay info")
        
        choice = input(f"Select sender to add relay info to (1-{len(senders)+1}): ").strip()
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(senders):
                # Update existing sender
                senders[choice_idx]["relay_host"] = relay_host
                senders[choice_idx]["username"] = username
                senders[choice_idx]["password"] = password
                save_senders(senders)
                print("✅ Relay information added to existing sender.")
            elif choice_idx == len(senders):
                # Create new sender
                sender_name = input("Enter sender name for this relay: ")
                sender_email = input("Enter sender email for this relay: ")
                relay_entry = {
                    "name": sender_name,
                    "email": sender_email,
                    "relay_host": relay_host,
                    "username": username,
                    "password": password
                }
                senders.append(relay_entry)
                save_senders(senders)
                print("✅ New sender with relay information created.")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid input. Relay info not saved.")

def send_test_email_to_address(to_email, subject):
    """Send a test email to a specific address"""
    body = f"This is a test email sent via {to_email} SMTP relay to verify the configuration."
    
    # Try to get a sender with relay info
    senders = load_senders()
    sender_with_relay = None
    for s in senders:
        if 'relay_host' in s:
            sender_with_relay = s
            break
    
    if sender_with_relay:
        # Use the sender we found that has relay info
        from_email = sender_with_relay['email']
        from_name = sender_with_relay['name']
        mail_cmd = f'echo "{body}" | mail -a "From: {from_name} <{from_email}>" -s "{subject}" {to_email}'
    else:
        # Use a default from address if no relay info is available
        mail_cmd = f'echo "{body}" | mail -a "From: Test <test@yourdomain.com>" -s "{subject}" {to_email}'
    
    result = subprocess.run(mail_cmd, shell=True)
    if result.returncode == 0:
        print(f"✅ Test email sent to {to_email}.")
    else:
        print(f"❌ Failed to send test email to {to_email}.")
    input("Press Enter to return...")

def load_senders():
    if not os.path.exists(SENDER_FILE):
        with open(SENDER_FILE, "w") as f:
            json.dump([], f)
        return []
    with open(SENDER_FILE, "r") as f:
        return json.load(f)

def save_senders(senders):
    # Encrypt passwords before saving
    encrypted_senders = []
    for sender in senders:
        encrypted_sender = sender.copy()
        if 'password' in encrypted_sender:
            encrypted_sender['password'] = encrypt_password(encrypted_sender['password'])
        encrypted_senders.append(encrypted_sender)
    
    with open(SENDER_FILE, "w") as f:
        json.dump(encrypted_senders, f, indent=2)

def load_senders():
    if not os.path.exists(SENDER_FILE):
        with open(SENDER_FILE, "w") as f:
            json.dump([], f)
        return []
    with open(SENDER_FILE, "r") as f:
        senders = json.load(f)
    
    # Decrypt passwords after loading
    decrypted_senders = []
    for sender in senders:
        decrypted_sender = sender.copy()
        if 'password' in decrypted_sender:
            decrypted_sender['password'] = decrypt_password(decrypted_sender['password'])
        decrypted_senders.append(decrypted_sender)
    
    return decrypted_senders

def encrypt_password(password):
    """Encrypt password using base64 encoding"""
    return base64.b64encode(password.encode('utf-8')).decode('utf-8')

def decrypt_password(encrypted_password):
    """Decrypt password using base64 decoding"""
    return base64.b64decode(encrypted_password.encode('utf-8')).decode('utf-8')

def edit_sender_menu(stdscr):
    senders = load_senders()
    options = ["Add Sender", "Edit Sender", "Delete Sender", "View Senders", "Add Relay Info", "Back"]

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
            if current_row == 5:  # Back
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
                            relay_info = f" (relay: {s.get('relay_host', 'none')})" if 'relay_host' in s else " (no relay)"
                            stdscr.addstr(i+2, 2, f"{i+1}. {s['name']} <{s['email']}> {relay_info}")
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
                            relay_info = f" (relay: {s.get('relay_host', 'none')})" if 'relay_host' in s else " (no relay)"
                            print(f"{i+1}. {s['name']} <{s['email']}> {relay_info}")
                    input("Press Enter to return...")

            elif current_row == 4:  # Add Relay Info
                curses.endwin()
                if not senders:
                    print("No senders found. Please add a sender first.")
                else:
                    for i, s in enumerate(senders):
                        relay_info = f" (relay: {s.get('relay_host', 'none')})" if 'relay_host' in s else " (no relay)"
                        print(f"{i+1}. {s['name']} <{s['email']}> {relay_info}")
                    idx = int(input("Select sender to add/update relay info: ")) - 1
                    if 0 <= idx < len(senders):
                        relay_host = input("Enter relay host (e.g. smtp-relay.brevo.com:587): ")
                        username = input("Enter SMTP username: ")
                        password = input("Enter SMTP password: ")
                        senders[idx]["relay_host"] = relay_host
                        senders[idx]["username"] = username
                        senders[idx]["password"] = password  # Note: In future, this should be encrypted
                        save_senders(senders)
                        print("✅ Relay information added/updated for sender.")
                input("Press Enter to return...")
                    
            stdscr.clear()
            curses.doupdate()

def select_sender(stdscr):
    senders = load_senders()
    if not senders:
        print("No senders found. Please add via 'Edit Sender' menu first.")
        return None, None

    options = []
    for s in senders:
        relay_info = f" (relay: {s.get('relay_host', 'none')})" if 'relay_host' in s else " (no relay)"
        options.append(f"{s['name']} <{s['email']}> {relay_info}")
    
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
    result = subprocess.run(mail_cmd, shell=True)
    if result.returncode == 0:
        print("✅ Test email sent.\n")
    else:
        print("❌ Failed to send test email.\n")
    input("Press Enter to return...")

def check_mail_log():
    log_paths = ["/var/log/mail.log", "/var/log/maillog"]
    log_file = next((p for p in log_paths if os.path.exists(p)), None)

    if not log_file:
        print("❌ Tidak ditemukan mail log di sistem ini.")
        input("Press Enter to return...")
        return

    # Offer user a choice between viewing last 30 lines, following log, or parsing status
    print(f"\n📜 Mail Log Options for {log_file}:")
    print("1. View last 30 lines")
    print("2. Follow log in real-time (press Ctrl+C to stop)")
    print("3. Parse log for email status")
    
    choice = input("Choose option (1, 2, or 3): ").strip()
    
    if choice == "1":
        print(f"\n📜 Showing last 30 lines of {log_file}:\n")
        os.system(f"sudo tail -n 30 {log_file}")
        print("\n✅ Done.\n")
        input("Press Enter to return...")
    elif choice == "2":
        print(f"\n📜 Following {log_file} in real-time (Ctrl+C to stop)...\n")
        try:
            os.system(f"sudo tail -f {log_file}")
        except KeyboardInterrupt:
            print("\nStopped following log.\n")
            input("Press Enter to return...")
    elif choice == "3":
        parse_mail_log_status(log_file)
    else:
        print("Invalid choice. Returning to menu.")
        input("Press Enter to return...")


def parse_mail_log_status(log_file):
    """Parse mail log to display email status (delivered/deferred/bounced)"""
    print(f"\n🔍 Analyzing email status from {log_file}...")
    
    # Get the last 100 lines to find recent mail activity
    result = subprocess.run(['sudo', 'tail', '-n', '100', log_file], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Failed to read log file.")
        input("Press Enter to return...")
        return
    
    log_content = result.stdout
    statuses = []
    
    # Parse for different mail statuses in the log
    lines = log_content.split('\n')
    for line in lines:
        if 'status=sent' in line or 'status=delivered' in line:
            # Extract the message ID, sender, and recipient if possible
            parts = line.split()
            timestamp = ' '.join(parts[:3]) if len(parts) > 3 else 'Unknown'
            # Look for message ID
            msg_id = 'Unknown'
            for part in parts:
                if 'id=' in part or 'msgid=' in part:
                    msg_id = part
                    break
            # Look for "to=" to find recipient
            to_addr = 'Unknown'
            for part in parts:
                if 'to=' in part and 'orig_to=' not in part:  # Avoid orig_to which is original recipient
                    to_addr = part.split('=')[1]
                    break
            # Look for "from=" to find sender
            from_addr = 'Unknown'
            for part in parts:
                if 'from=' in part:
                    from_addr = part.split('=')[1]
                    break
            statuses.append(f"✅ DELIVERED: [{timestamp}] {from_addr} → {to_addr} ({msg_id})")
        elif 'status=deferred' in line:
            parts = line.split()
            timestamp = ' '.join(parts[:3]) if len(parts) > 3 else 'Unknown'
            msg_id = 'Unknown'
            for part in parts:
                if 'id=' in part or 'msgid=' in part:
                    msg_id = part
                    break
            to_addr = 'Unknown'
            for part in parts:
                if 'to=' in part and 'orig_to=' not in part:
                    to_addr = part.split('=')[1]
                    break
            from_addr = 'Unknown'
            for part in parts:
                if 'from=' in part:
                    from_addr = part.split('=')[1]
                    break
            statuses.append(f"⏳ DEFERRED: [{timestamp}] {from_addr} → {to_addr} ({msg_id})")
        elif 'status=bounced' in line or 'status=expired' in line or 'warning: delivery' in line or ' bounce ' in line or 'reject' in line:
            parts = line.split()
            timestamp = ' '.join(parts[:3]) if len(parts) > 3 else 'Unknown'
            msg_id = 'Unknown'
            for part in parts:
                if 'id=' in part or 'msgid=' in part:
                    msg_id = part
                    break
            to_addr = 'Unknown'
            for part in parts:
                if 'to=' in part and 'orig_to=' not in part:
                    to_addr = part.split('=')[1]
                    break
            from_addr = 'Unknown'
            for part in parts:
                if 'from=' in part:
                    from_addr = part.split('=')[1]
                    break
            statuses.append(f"❌ FAILED: [{timestamp}] {from_addr} → {to_addr} ({msg_id})")

    print(f"\n📊 Found {len(statuses)} email status entries:")
    print("-" * 60)
    
    # Print the most recent statuses (reverse order to show newest first)
    if statuses:
        for status in reversed(statuses[-10:]):  # Show at most last 10 statuses
            print(status)
    else:
        print("No email status entries found in recent logs.")
    
    print("-" * 60)
    input("Press Enter to return...")


def mail_queue_menu(stdscr):
    """Menu to manage the mail queue"""
    options = ["View Queue", "Flush Queue", "Back"]
    current_row = 0

    while True:
        draw_menu(stdscr, current_row, options, "Mail Queue Management")
        stdscr.addstr(len(options) + 3, 2, "Use ↑↓ to navigate, Enter to select.")
        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row == 0:  # View Queue
                curses.endwin()
                view_mail_queue()
            elif current_row == 1:  # Flush Queue
                curses.endwin()
                flush_mail_queue()
            elif current_row == 2:  # Back
                return
                
            stdscr.clear()
            curses.doupdate()


def view_mail_queue():
    """Display the current mail queue using postqueue -p"""
    print("\n📧 Current Mail Queue:")
    print("-" * 50)
    
    try:
        result = subprocess.run(['sudo', 'postqueue', '-p'], capture_output=True, text=True)
        
        if result.returncode == 0:
            if "Mail queue is empty" in result.stdout or result.stdout.strip() == "":
                print("The mail queue is currently empty.")
            else:
                print(result.stdout)
        else:
            print("❌ Failed to retrieve mail queue information.")
            print(f"Error: {result.stderr}")
    except FileNotFoundError:
        print("❌ postqueue command not found. Make sure Postfix is installed.")
    
    print("-" * 50)
    input("Press Enter to return...")


def flush_mail_queue():
    """Flush the mail queue using postqueue -f"""
    print("\n🔄 Flushing mail queue...")
    
    try:
        result = subprocess.run(['sudo', 'postqueue', '-f'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Mail queue has been flushed.")
            print("All queued emails are now being processed.")
        else:
            print("❌ Failed to flush mail queue.")
            print(f"Error: {result.stderr}")
    except FileNotFoundError:
        print("❌ postqueue command not found. Make sure Postfix is installed.")
    
    input("Press Enter to return...")


def uninstall_reset_menu(stdscr):
    """Menu for uninstalling or resetting Postfix configuration"""
    options = ["Uninstall Postfix", "Reset SASL Configuration", "Reset All Configs", "Remove sender.json", "Back"]
    current_row = 0

    while True:
        draw_menu(stdscr, current_row, options, "Uninstall/Reset Options")
        stdscr.addstr(len(options) + 3, 2, "Use ↑↓ to navigate, Enter to select.")
        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if current_row == 0:  # Uninstall Postfix
                curses.endwin()
                confirm_uninstall_postfix()
            elif current_row == 1:  # Reset SASL Configuration
                curses.endwin()
                reset_sasl_config()
            elif current_row == 2:  # Reset All Configs
                curses.endwin()
                reset_all_configs()
            elif current_row == 3:  # Remove sender.json
                curses.endwin()
                remove_sender_json()
            elif current_row == 4:  # Back
                return
                
            stdscr.clear()
            curses.doupdate()


def confirm_uninstall_postfix():
    """Confirm and uninstall Postfix"""
    print("\n⚠️  WARNING: This will completely uninstall Postfix!")
    confirm = input("Are you sure you want to uninstall Postfix? (type 'YES' to confirm): ").strip()
    
    if confirm == "YES":
        print("\n📦 Uninstalling Postfix...")
        result = subprocess.run(['sudo', 'apt-get', 'remove', '--purge', '-y', 'postfix'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Postfix has been uninstalled.")
        else:
            print("❌ Failed to uninstall Postfix.")
            print(f"Error: {result.stderr}")
    else:
        print("❌ Uninstall cancelled.")
    
    input("Press Enter to return...")


def reset_sasl_config():
    """Reset SASL configuration files"""
    print("\n🔄 Resetting SASL configuration...")
    
    # Remove SASL password files
    result1 = subprocess.run(['sudo', 'rm', '-f', '/etc/postfix/sasl_passwd', '/etc/postfix/sasl_passwd.db'], capture_output=True, text=True)
    
    # Remove SASL-related lines from main.cf
    result2 = subprocess.run(['sudo', 'sed', '-i', 
                            '-e', '/relayhost/d', 
                            '-e', '/smtp_use_tls/d', 
                            '-e', '/smtp_sasl_auth_enable/d', 
                            '-e', '/smtp_sasl_password_maps/d', 
                            '-e', '/smtp_sasl_security_options/d', 
                            '-e', '/smtp_sasl_tls_security_options/d', 
                            '/etc/postfix/main.cf'], capture_output=True, text=True)
    
    # Restart Postfix
    result3 = subprocess.run(['sudo', 'systemctl', 'restart', 'postfix'], capture_output=True, text=True)
    
    if result1.returncode == 0 and result2.returncode == 0 and result3.returncode == 0:
        print("✅ SASL configuration has been reset.")
        print("  - SASL password files removed")
        print("  - SASL settings removed from main.cf")
        print("  - Postfix restarted")
    else:
        print("⚠️  Some errors occurred during reset, but changes were applied where possible.")
    
    input("Press Enter to return...")


def reset_all_configs():
    """Reset all Postfix configurations"""
    print("\n🔄 Resetting all Postfix configurations...")
    
    # Reset SASL config
    reset_sasl_config()
    
    # Additional reset operations could be added here
    # For now, let's also reset the main.cf to basic configuration
    basic_config = """# Basic Postfix configuration
# Generated by SMTP Relay Setup
myhostname = localhost
mydomain = localhost
myorigin = $mydomain
inet_interfaces = loopback-only
mydestination = $myhostname, localhost, localhost.localdomain
home_mailbox = Maildir/
"""
    
    with open('/tmp/basic_main.cf', 'w') as f:
        f.write(basic_config)
    
    # Copy the basic config to main.cf
    result = subprocess.run(['sudo', 'cp', '/tmp/basic_main.cf', '/etc/postfix/main.cf'], capture_output=True, text=True)
    
    if result.returncode == 0:
        # Restart Postfix
        restart_result = subprocess.run(['sudo', 'systemctl', 'restart', 'postfix'], capture_output=True, text=True)
        if restart_result.returncode == 0:
            print("✅ All configurations have been reset to defaults.")
        else:
            print("⚠️  Configuration reset applied but failed to restart Postfix.")
    else:
        print("⚠️  Failed to reset all configurations completely.")
    
    # Clean up temp file
    os.remove('/tmp/basic_main.cf')
    
    input("Press Enter to return...")


def remove_sender_json():
    """Remove the sender.json file"""
    print(f"\n🗑️  Removing {SENDER_FILE}...")
    
    if os.path.exists(SENDER_FILE):
        os.remove(SENDER_FILE)
        print(f"✅ {SENDER_FILE} has been removed.")
    else:
        print(f"⚠️  {SENDER_FILE} does not exist.")
    
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
            elif current_row == 5:  # Mail Queue
                mail_queue_menu(stdscr)
            elif current_row == 6:  # Uninstall/Reset
                uninstall_reset_menu(stdscr)
            elif current_row == 7:  # Exit
                break

            stdscr.addstr(5, 0, "Press any key to return to menu...")
            stdscr.getch()

curses.wrapper(main)
