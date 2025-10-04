#!/usr/bin/env python3
"""
SMTP Relay API Server - Provides API endpoints for SMTP relay functionality
Allows the Web UI to communicate with the same backend that powers the CLI
"""
import json
import subprocess
import os
import base64
from flask import Flask, request, jsonify, abort
from flask_cors import CORS  # <-- 1. IMPORT KEMBALI
from datetime import datetime
import logging

# --- Setup basic logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)  # <-- 2. AKTIFKAN CORS UNTUK SEMUA ROUTE

# --- Use Absolute Paths to avoid ambiguity ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SENDER_FILE = os.path.join(BASE_DIR, "sender.json")
SASL_CONFIG_FILE = os.path.join(BASE_DIR, "sasl_config.json")

API_PORT = int(os.environ.get('API_PORT', 5001))

class SMTPRelayAPI:
    # ... sisa kode tidak perlu diubah ...
    """API class that provides the same functionality as the CLI"""
    
    @staticmethod
    def load_sasl_config():
        """Load SASL configuration from file"""
        if not os.path.exists(SASL_CONFIG_FILE):
            with open(SASL_CONFIG_FILE, "w") as f:
                json.dump({"relay_hosts": []}, f)
            return {"relay_hosts": []}
        with open(SASL_CONFIG_FILE, "r") as f:
            return json.load(f)
    
    @staticmethod
    def save_sasl_config(config):
        """Save SASL configuration to file"""
        with open(SASL_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    
    @staticmethod
    def load_senders():
        """Load senders from JSON file"""
        logging.info(f"Attempting to load senders from: {SENDER_FILE}")
        if not os.path.exists(SENDER_FILE):
            logging.warning(f"'{SENDER_FILE}' not found. Creating a new empty file.")
            with open(SENDER_FILE, "w") as f:
                json.dump([], f)
            return []
        
        try:
            with open(SENDER_FILE, "r") as f:
                content = f.read()
                if not content.strip():
                    logging.warning(f"'{SENDER_FILE}' is empty. Returning empty list.")
                    return []
                data = json.loads(content)
                logging.info(f"Successfully loaded {len(data)} senders.")
                return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.error(f"Error loading or parsing '{SENDER_FILE}': {e}. Returning empty list.")
            return []
    
    @staticmethod
    def save_senders(senders):
        """Save senders to JSON file"""
        logging.info(f"Attempting to save {len(senders)} senders to: {SENDER_FILE}")
        try:
            with open(SENDER_FILE, "w") as f:
                json.dump(senders, f, indent=2)
            logging.info("Successfully saved senders.")
        except Exception as e:
            logging.error(f"Failed to save senders to '{SENDER_FILE}': {e}")
    
    @staticmethod
    def encrypt_password(password):
        """Encrypt password using base64 encoding"""
        return base64.b64encode(password.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def decrypt_password(encrypted_password):
        """Decrypt password using base64 decoding"""
        return base64.b64decode(encrypted_password.encode('utf-8')).decode('utf-8')
    
    @staticmethod
    def install_postfix():
        """Install Postfix"""
        try:
            result = subprocess.run(["sudo", "apt-get", "install", "-y", "postfix"], 
                                  capture_output=True, text=True, check=True)
            return {"status": "success", "message": "Postfix installed successfully"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Failed to install Postfix: {e.stderr}"}
    
    @staticmethod
    def configure_sasl(relay_host, username, password):
        """Configure SASL authentication"""
        try:
            # Write SASL password
            with open('/etc/postfix/sasl_passwd', 'w') as f:
                f.write(f'[{relay_host}] {username}:{password}\n')
            
            # Generate the hash file
            subprocess.run(['sudo', 'postmap', '/etc/postfix/sasl_passwd'], check=True)
            subprocess.run(['sudo', 'chmod', '600', '/etc/postfix/sasl_passwd', '/etc/postfix/sasl_passwd.db'], check=True)
            
            # Update main.cf with relay settings
            with open('/etc/postfix/main.cf', 'a') as f:
                f.write(f'\nrelayhost = [{relay_host}]:587\n')
                f.write('smtp_use_tls = yes\n')
                f.write('smtp_sasl_auth_enable = yes\n')
                f.write('smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd\n')
                f.write('smtp_sasl_security_options = noanonymous\n')
                f.write('smtp_sasl_tls_security_options = noanonymous\n')
            
            # Restart postfix
            subprocess.run(['sudo', 'systemctl', 'restart', 'postfix'], check=True)
            
            return {"status": "success", "message": "SASL configured successfully"}
        
        except FileNotFoundError as e:
            return {"status": "error", "message": f"Command not found: {str(e)}"}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Error configuring SASL: {str(e)}"}
        except PermissionError:
            return {"status": "error", "message": "Permission denied - run with appropriate privileges"}
        except Exception as e:
            return {"status": "error", "message": f"Error: {str(e)}"}
    
    @staticmethod
    def send_test_email(from_email, from_name, to_email, subject, body):
        """Send a test email"""
        try:
            mail_cmd = f'echo "{body}" | mail -a "From: {from_name} <{from_email}>" -s "{subject}" {to_email}'
            result = subprocess.run(mail_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {"status": "success", "message": "Test email sent successfully"}
            else:
                return {"status": "error", "message": f"Failed to send email: {result.stderr}"}
        except Exception as e:
            return {"status": "error", "message": f"Error sending email: {str(e)}"}
    
    @staticmethod
    def get_mail_log(option="last30"):
        """Get mail log based on option"""
        log_paths = ["/var/log/mail.log", "/var/log/maillog"]
        log_file = next((p for p in log_paths if os.path.exists(p)), None)

        if not log_file:
            return {"status": "error", "message": "Mail log not found on this system"}

        if option == "last30":
            result = subprocess.run(['sudo', 'tail', '-n', '30', log_file], 
                                  capture_output=True, text=True)
        elif option == "follow":
            # For follow mode, we can't really follow in HTTP response
            # So we'll just return the last 100 lines
            result = subprocess.run(['sudo', 'tail', '-n', '100', log_file], 
                                  capture_output=True, text=True)
        elif option == "parse_status":
            return SMTPRelayAPI.parse_mail_log_status(log_file)
        else:
            result = subprocess.run(['sudo', 'tail', '-n', '30', log_file], 
                                  capture_output=True, text=True)
        
        if result.returncode == 0:
            return {"status": "success", "log": result.stdout}
        else:
            return {"status": "error", "message": result.stderr}
    
    @staticmethod
    def parse_mail_log_status(log_file):
        """Parse mail log to display email status (delivered/deferred/bounced)"""
        try:
            # Get the last 100 lines to find recent mail activity
            result = subprocess.run(['sudo', 'tail', '-n', '100', log_file], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"status": "error", "message": "Failed to read log file"}
            
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
                        if 'to=' in part and 'orig_to=' not in part:
                            to_addr = part.split('=')[1]
                            break
                    # Look for "from=" to find sender
                    from_addr = 'Unknown'
                    for part in parts:
                        if 'from=' in part:
                            from_addr = part.split('=')[1]
                            break
                    statuses.append({
                        "status": "delivered",
                        "timestamp": timestamp,
                        "from": from_addr,
                        "to": to_addr,
                        "message_id": msg_id
                    })
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
                    statuses.append({
                        "status": "deferred", 
                        "timestamp": timestamp,
                        "from": from_addr,
                        "to": to_addr,
                        "message_id": msg_id
                    })
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
                    statuses.append({
                        "status": "failed",
                        "timestamp": timestamp,
                        "from": from_addr,
                        "to": to_addr,
                        "message_id": msg_id
                    })

            return {
                "status": "success",
                "statuses": statuses[-10:]  # Return last 10 statuses
            }
        except Exception as e:
            return {"status": "error", "message": f"Error parsing log: {str(e)}"}
    
    @staticmethod
    def get_mail_queue():
        """Get the current mail queue"""
        try:
            result = subprocess.run(['sudo', 'postqueue', '-p'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                if "Mail queue is empty" in result.stdout or result.stdout.strip() == "":
                    return {"status": "success", "queue": "Mail queue is empty"}
                else:
                    return {"status": "success", "queue": result.stdout}
            else:
                # Check if it's a "Mail system is down" error
                if "Mail system is down" in result.stderr or "Connect to the Postfix showq service" in result.stderr:
                    return {"status": "error", "message": "Mail system is not running properly. Postfix may need to be configured."}
                else:
                    return {"status": "error", "message": result.stderr}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Command timed out - Postfix may not be responding"}
        except FileNotFoundError:
            return {"status": "error", "message": "postqueue command not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def flush_mail_queue():
        """Flush the mail queue"""
        try:
            result = subprocess.run(['sudo', 'postqueue', '-f'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return {"status": "success", "message": "Mail queue has been flushed"}
            else:
                # Check if it's a "Mail system is down" error
                if "Mail system is down" in result.stderr or "Connect to the Postfix showq service" in result.stderr:
                    return {"status": "error", "message": "Mail system is not running properly. Postfix may need to be configured."}
                else:
                    return {"status": "error", "message": result.stderr}
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Command timed out - Postfix may not be responding"}
        except FileNotFoundError:
            return {"status": "error", "message": "postqueue command not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def uninstall_postfix():
        """Uninstall Postfix"""
        try:
            result = subprocess.run(['sudo', 'apt-get', 'remove', '--purge', '-y', 'postfix'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return {"status": "success", "message": "Postfix has been uninstalled"}
            else:
                return {"status": "error", "message": result.stderr}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def reset_sasl_config():
        """Reset SASL configuration"""
        try:
            # Remove SASL password files
            subprocess.run(['sudo', 'rm', '-f', '/etc/postfix/sasl_passwd', '/etc/postfix/sasl_passwd.db'], 
                         capture_output=True, text=True)
            
            # Remove SASL-related lines from main.cf
            subprocess.run(['sudo', 'sed', '-i', 
                            '-e', '/relayhost/d', 
                            '-e', '/smtp_use_tls/d', 
                            '-e', '/smtp_sasl_auth_enable/d', 
                            '-e', '/smtp_sasl_password_maps/d', 
                            '-e', '/smtp_sasl_security_options/d', 
                            '-e', '/smtp_sasl_tls_security_options/d', 
                            '/etc/postfix/main.cf'], capture_output=True, text=True)
            
            # Restart Postfix
            subprocess.run(['sudo', 'systemctl', 'restart', 'postfix'], capture_output=True, text=True)
            
            return {"status": "success", "message": "SASL configuration has been reset"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# API Routes
@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current system status"""
    senders = SMTPRelayAPI.load_senders()
    
    # Check if postqueue command exists and is working
    try:
        queue_result = subprocess.run(['sudo', 'postqueue', '-p'], capture_output=True, text=True, timeout=10)
        if queue_result.returncode == 0:
            queue_status = queue_result.stdout if queue_result.stdout.strip() else "Mail queue is empty"
        else:
            # Check if it's a "Mail system is down" error
            if "Mail system is down" in queue_result.stderr or "Connect to the Postfix showq service" in queue_result.stderr:
                queue_status = "Postfix not running properly"
            else:
                queue_status = f"Error: {queue_result.stderr}"
    except subprocess.TimeoutExpired:
        queue_status = "Command timed out - Postfix may not be responding"
    except FileNotFoundError:
        queue_status = "postqueue command not found"
    except Exception as e:
        queue_status = f"Error checking queue: {str(e)}"
    
    # Check if postfix is running
    try:
        result = subprocess.run(['sudo', 'postfix', 'status'], capture_output=True, text=True)
        postfix_running = result.returncode == 0
    except:
        postfix_running = False  # If status command fails, assume not running
    
    return jsonify({
        'senders_count': len(senders),
        'queue_status': queue_status,
        'postfix_running': postfix_running
    })

@app.route('/api/senders', methods=['GET'])
def get_senders():
    """Get all senders"""
    senders = SMTPRelayAPI.load_senders()
    return jsonify(senders)

@app.route('/api/senders', methods=['POST'])
def add_sender():
    """Add a new sender"""
    data = request.json
    senders = SMTPRelayAPI.load_senders()
    
    new_sender = {
        'name': data['name'],
        'email': data['email']
    }
    
    senders.append(new_sender)
    SMTPRelayAPI.save_senders(senders)
    
    return jsonify({'status': 'success'}), 201

@app.route('/api/senders/<int:sender_id>', methods=['PUT'])
def update_sender(sender_id):
    """Update a sender"""
    data = request.json
    senders = SMTPRelayAPI.load_senders()
    
    if 0 <= sender_id < len(senders):
        senders[sender_id]['name'] = data['name']
        senders[sender_id]['email'] = data['email']
        SMTPRelayAPI.save_senders(senders)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Sender not found'}), 404

@app.route('/api/senders/<int:sender_id>', methods=['DELETE'])
def delete_sender(sender_id):
    """Delete a sender"""
    senders = SMTPRelayAPI.load_senders()
    
    if 0 <= sender_id < len(senders):
        del senders[sender_id]
        SMTPRelayAPI.save_senders(senders)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Sender not found'}), 404

@app.route('/api/configure_sasl', methods=['POST'])
def configure_sasl():
    """Configure SASL settings"""
    data = request.json
    result = SMTPRelayAPI.configure_sasl(data['relay_host'], data['username'], data['password'])
    return jsonify(result)

@app.route('/api/send_test_email', methods=['POST'])
def send_test_email():
    """Send a test email"""
    data = request.json
    result = SMTPRelayAPI.send_test_email(
        data['from_email'], 
        data['from_name'], 
        data['to_email'], 
        data['subject'], 
        data['body']
    )
    
    # Add delivery status check after sending
    if result['status'] == 'success':
        # Check mail queue to confirm the email was queued and provide detailed status
        try:
            queue_result = subprocess.run(['sudo', 'postqueue', '-p'], capture_output=True, text=True, timeout=5)
            if queue_result.returncode == 0:
                if queue_result.stdout.strip() != "Mail queue is empty" and "-Queue ID-" in queue_result.stdout:
                    result['delivery_status'] = 'queued_for_delivery'
                    result['message'] = "Email sent successfully and queued for delivery! Message delivered to SMTP relay."
                    
                    # Find and extract queue ID for the specific email
                    lines = queue_result.stdout.split('\n')
                    for line in lines[4:]:  # Skip header lines
                        if data['to_email'] in line and line.strip() != "":
                            # Extract queue ID
                            parts = line.split()
                            if len(parts) > 0 and parts[0] != "":
                                queue_id = parts[0].strip('*')
                                result['queue_id'] = queue_id
                                result['delivery_details'] = f"Queue ID: {queue_id}"
                                break
                else:
                    result['delivery_status'] = 'queued_for_delivery'
                    result['message'] = "Email sent successfully and queued for delivery!"
            else:
                result['delivery_status'] = 'queued_for_delivery'
                result['message'] = "Email sent successfully and likely queued for delivery. Mail queue check timed out."
        except subprocess.TimeoutExpired:
            result['delivery_status'] = 'unknown'
            result['message'] = "Email sent successfully! Unable to confirm queue status due to timeout."
        except Exception as e:
            result['delivery_status'] = 'unknown'
            result['message'] = f"Email sent successfully but status check failed: {str(e)}"
    
    return jsonify(result)

@app.route('/api/mail_queue', methods=['GET'])
def get_mail_queue():
    """Get mail queue status"""
    result = SMTPRelayAPI.get_mail_queue()
    return jsonify(result)

@app.route('/api/flush_queue', methods=['POST'])
def flush_queue():
    """Flush mail queue"""
    result = SMTPRelayAPI.flush_mail_queue()
    return jsonify(result)

@app.route('/api/install_postfix', methods=['POST'])
def install_postfix():
    """Install Postfix"""
    result = SMTPRelayAPI.install_postfix()
    return jsonify(result)

@app.route('/api/reset_sasl', methods=['POST'])
def reset_sasl():
    """Reset SASL configuration"""
    result = SMTPRelayAPI.reset_sasl_config()
    return jsonify(result)

@app.route('/api/uninstall_postfix', methods=['POST'])
def uninstall_postfix():
    """Uninstall Postfix"""
    result = SMTPRelayAPI.uninstall_postfix()
    return jsonify(result)

@app.route('/api/mail_log', methods=['GET'])
def get_mail_log():
    """Get mail log"""
    option = request.args.get('option', 'last30')
    result = SMTPRelayAPI.get_mail_log(option)
    return jsonify(result)

@app.route('/api/parse_log_status', methods=['GET'])
def parse_log_status():
    """Parse log for status information"""
    log_paths = ["/var/log/mail.log", "/var/log/maillog"]
    log_file = next((p for p in log_paths if os.path.exists(p)), None)

    if not log_file:
        return jsonify({"status": "error", "message": "Mail log not found on this system"})
    
    result = SMTPRelayAPI.parse_mail_log_status(log_file)
    return jsonify(result)

if __name__ == '__main__':
    logging.info(f"Starting SMTP Relay API Server on port {API_PORT}")
    logging.info(f"Sender file path: {SENDER_FILE}")
    logging.info(f"SASL config path: {SASL_CONFIG_FILE}")
    app.run(host='0.0.0.0', port=API_PORT, debug=False)

