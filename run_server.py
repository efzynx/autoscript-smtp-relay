#!/usr/bin/env python3
"""
Server startup script with automatic port selection
Finds an available port in the range 8001-8999 and starts the application
"""
import uvicorn
import sys
from port_selector import find_free_port

def main():
    # Find an available port in the range 8001-8999
    available_port = find_free_port(8001, 8999)
    
    if available_port:
        print(f"Starting server on available port: {available_port}")
        print(f"Server will be accessible at: http://localhost:{available_port}")
        uvicorn.run("main:app", host="0.0.0.0", port=available_port, reload=False)  # Set reload=False to avoid conflicts when running as script
    else:
        print("No available ports found in range 8001-8999. Please free up some ports.")
        sys.exit(1)

if __name__ == "__main__":
    main()