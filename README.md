# SMTP Relay Setup Tool

A comprehensive tool for setting up and managing SMTP relays with Postfix. The tool provides both a Terminal UI (TUI) and a Web UI for managing your email relay configurations with an intuitive start menu for mode selection.

## 🚀 Features

### Interface Options
- **Start Menu**: Choose between Terminal UI or Web UI mode from a single entry point
- **Terminal UI**: Interactive curses-based interface with menus and options
- **Web UI**: Browser-based interface accessible at http://localhost:5000

### 🔧 Configuration & Management
- **Automatic main.cf Configuration**: When setting up SASL, default configuration is immediately added to `/etc/postfix/main.cf`
- **Multi-Account Support**: Manage multiple relay services (Brevo, Gmail, Mailgun) in one tool
- **Sender Management**: Add, edit, delete, and switch between different sender accounts
- **Password Encryption**: Passwords stored using Base64 encoding in `sender.json`

### 📊 Monitoring & Debugging
- **Log Parsing**: Parse `mail.log` to display email status (delivered/deferred/bounced)
- **Mail Queue Management**: View and flush queued emails with `postqueue -p` and `postqueue -f`
- **Comprehensive Logging**: View last 30 lines or follow logs in real-time

### 🛠️ Administration
- **Installation**: One-click Postfix installation with apt-get
- **SASL Configuration**: Easy setup for SMTP authentication
- **Test Email Functionality**: Send test emails to verify relay configuration
- **Reset/Uninstall Options**: Complete removal or reset of configurations

### 🐳 Deployment
- **Docker Support**: Containerized deployment with provided Dockerfile
- **Docker Compose**: Simplified setup with single-command deployment
- **Cross-Platform**: Portable across different environments

## 📋 Requirements

- Python 3.6+
- Postfix
- mailutils
- sudo access for Postfix configuration

## 🛠️ Installation and Usage

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd smtp-relay-setup

# Install dependencies
pip install -r requirements.txt

# Run the start menu to choose your preferred interface
python3 main_menu.py
```

### Terminal UI Mode
```bash
python3 main_menu.py
# Then select "Run in Terminal UI Mode (TUI)"
```

### Web UI Mode
```bash
python3 main_menu.py
# Then select "Run in Web UI Mode"
# Visit http://localhost:5000 in your browser
```

## 🐳 Docker Deployment

### Prerequisites
Make sure you have Docker and Docker Compose installed. If you encounter permission errors, you may need to add your user to the docker group:
```bash
sudo usermod -aG docker $USER
# Log out and log back in for changes to take effect
```

### Using Docker Compose (Recommended)
The application now uses a microservices architecture with separate containers for the API server and Web UI:
```bash
# Build and start the API server and Web UI
docker compose up --build -d

# The Web UI will be available at http://localhost:5000
# The API server will be available at http://localhost:5001
# SMTP relay will be available on port 25
```

### Using Docker directly
```bash
# Build the Docker image
docker build -t smtp-relay-setup .

# Run in Web UI mode
docker run -it -p 5000:5000 -p 5001:5001 -p 25:25 --name smtp-relay smtp-relay-setup web

# Run in Terminal UI mode
docker run -it --name smtp-relay smtp-relay-setup tui

# Run API server mode
docker run -it -p 5001:5001 --name smtp-relay-api smtp-relay-setup api
```

### Architecture Overview
The system now uses a hybrid architecture:
- **API Server**: Handles all SMTP relay functionality and provides REST API endpoints
- **Web UI**: Modern interface that communicates with the API server
- **TUI**: Traditional terminal interface for direct interaction
- **Shared Backend**: Both UIs use the same backend logic and data

### Troubleshooting Docker Issues

#### Permission Issues
If you encounter permission errors:
- Add your user to the docker group: `sudo usermod -aG docker $USER`
- Log out and log back in for changes to take effect
- Or run with sudo: `sudo docker compose up --build -d`

#### Postfix in Docker Containers
When running Postfix in Docker containers, you may encounter issues with the service not starting properly. This is a known issue with Postfix in containerized environments. The containerized setup has been updated to handle this with:

1. Proper directory permissions for Postfix
2. Direct execution of the Postfix master process
3. Fallback checks using `ps` instead of `pgrep` for process verification
4. Non-fatal warnings if Postfix doesn't start properly, allowing the UI to still function

If the container still has issues starting Postfix:
1. Make sure your container is running with necessary privileges
2. The entrypoint script handles Postfix initialization
3. If Postfix continues to have issues, consider running the application locally:
   ```bash
   python3 main_menu.py
   ```

## 🔐 Security Notes

- Passwords are stored with Base64 encoding in sender.json
- For production use, consider stronger encryption methods
- Ensure Web UI access is secured when deployed publicly
- The tool requires sudo access for Postfix configuration - ensure proper system security

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions, please open an issue in the repository.