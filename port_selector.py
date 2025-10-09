import socket
from contextlib import closing

def find_free_port(start_port=8001, end_port=8999):
    """
    Find the first available port in the specified range.
    
    Args:
        start_port (int): Starting port number to check (default: 8001)
        end_port (int): Ending port number to check (default: 8999)
    
    Returns:
        int: First available port number, or None if no port is available
    """
    for port in range(start_port, end_port + 1):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.bind(('', port))
                return port  # Port is available
            except OSError:
                continue  # Port is in use, try the next one
    
    return None  # No available port found in the range

def is_port_available(port):
    """
    Check if a specific port is available.
    
    Args:
        port (int): Port number to check
    
    Returns:
        bool: True if port is available, False otherwise
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind(('', port))
            return True
        except OSError:
            return False

if __name__ == "__main__":
    # Example usage
    available_port = find_free_port()
    if available_port:
        print(f"Found available port: {available_port}")
    else:
        print("No available ports found in the specified range")