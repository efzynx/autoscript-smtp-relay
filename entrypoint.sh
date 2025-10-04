#!/bin/bash

# Properly initialize postfix for container environment
# Create necessary directories with correct permissions
mkdir -p /var/spool/postfix/pid /var/lib/postfix /etc/postfix /var/run/postfix

# Ensure proper permissions for postfix
chown -R root:root /etc/postfix
chown root:root /var/lib/postfix
chown root:postfix /var/spool/postfix
chown root:postfix /var/run/postfix
chmod 755 /var/spool/postfix
chmod 755 /var/run/postfix

# Initialize postfix configuration if needed
if [ ! -f /etc/postfix/main.cf ]; then
    postconf -n > /tmp/main.cf
    cat /tmp/main.cf > /etc/postfix/main.cf
fi

# Start the postfix services using the service command or directly
if command -v service &> /dev/null; then
    service postfix start 2>/dev/null || {
        echo "service command failed, trying direct master start..."
        /usr/lib/postfix/sbin/master -c /etc/postfix &
    }
else
    # Try to start postfix directly
    /usr/lib/postfix/sbin/master -c /etc/postfix &
fi

# Wait a moment for postfix to initialize
sleep 3

# Make sure postfix is running - use ps instead of pgrep (which may not be available)
if ! ps aux | grep -q '[m]aster' || ! pgrep -x "master" >/dev/null 2>&1; then
    # Try to check for master process using ps alone
    if ! ps aux | grep -q '[m]aster'; then
        echo "Postfix master process is not running!"
        # Don't exit, just warn - as the UI might still work but without postfix functionality
        echo "WARNING: Postfix may not be running properly. Some email functions may not work."
    else
        echo "Postfix master started successfully (detected via ps)"
    fi
else
    echo "Postfix master started successfully"
fi

# Check command line arguments
case "${1:-}" in
    "tui")
        echo "Starting Terminal UI Mode..."
        exec python3 main_menu.py
        ;;
    "web")
        echo "Starting Web UI Mode..."
        # Run python web server in foreground
        exec python3 web_ui.py
        ;;
    "api")
        echo "Starting API Server Mode..."
        # Run python API server in foreground
        exec python3 api_server.py
        ;;
    *)
        echo "Usage: docker run -it smtp-relay-setup [tui|web|api]"
        echo "  tui - Run Terminal UI"
        echo "  web - Run Web UI"
        echo "  api - Run API Server (default if no argument)"
        echo "Starting API Server Mode by default..."
        # Run python API server in foreground
        exec python3 api_server.py
        ;;
esac