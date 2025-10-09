#!/usr/bin/env python3
"""
Module for detecting the operating system and system capabilities.
This module helps identify the Linux distribution and available package managers.
"""
import os
import platform
import subprocess
from typing import Optional, Dict, Any


class SystemDetector:
    """Detects the operating system and system capabilities."""

    def __init__(self):
        self.os_info = {}
        self.package_manager = None
        self.services = {}

    def detect_os(self) -> Dict[str, Any]:
        """Detect the operating system and return information about it."""
        os_info = {
            'platform': platform.system(),
            'distro': 'unknown',
            'version': 'unknown',
            'family': 'unknown'
        }

        # Try to detect Linux distribution
        try:
            # Method 1: Using os-release
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    for line in f:
                        if line.startswith('ID='):
                            os_info['distro'] = line.split('=')[1].strip().strip('"')
                        elif line.startswith('VERSION_ID='):
                            os_info['version'] = line.split('=')[1].strip().strip('"')
                        elif line.startswith('NAME='):
                            os_info['name'] = line.split('=')[1].strip().strip('"')
        except:
            pass

        # Method 2: Check for specific files
        if os_info['distro'] == 'unknown':
            if os.path.exists('/etc/debian_version'):
                os_info['distro'] = 'debian'
                os_info['family'] = 'debian'
                with open('/etc/debian_version', 'r') as f:
                    os_info['version'] = f.read().strip()
            elif os.path.exists('/etc/redhat-release') or os.path.exists('/etc/centos-release') or os.path.exists('/etc/fedora-release'):
                os_info['distro'] = 'redhat'
                os_info['family'] = 'redhat'
                if os.path.exists('/etc/redhat-release'):
                    with open('/etc/redhat-release', 'r') as f:
                        content = f.read().strip()
                        os_info['version'] = content.split()[-1] if content.split()[-1].isdigit() else 'unknown'
                elif os.path.exists('/etc/centos-release'):
                    with open('/etc/centos-release', 'r') as f:
                        content = f.read().strip()
                        os_info['version'] = content.split()[-1] if content.split()[-1].isdigit() else 'unknown'
                elif os.path.exists('/etc/fedora-release'):
                    with open('/etc/fedora-release', 'r') as f:
                        content = f.read().strip()
                        os_info['version'] = content.split()[-1] if content.split()[-1].isdigit() else 'unknown'

        # Determine family based on distro
        if os_info['distro'] in ['ubuntu', 'debian', 'mint', 'kali', 'raspbian']:
            os_info['family'] = 'debian'
        elif os_info['distro'] in ['centos', 'rhel', 'fedora', 'rocky', 'almalinux', 'amazon']:
            os_info['family'] = 'redhat'
        elif os_info['distro'] in ['arch', 'manjaro']:
            os_info['family'] = 'arch'
        else:
            # Default to debian family for unknown distros
            os_info['family'] = 'debian'

        self.os_info = os_info
        return os_info

    def detect_package_manager(self) -> Optional[str]:
        """Detect which package manager is available on the system."""
        package_managers = {
            'apt': ['apt', 'apt-get'],
            'yum': ['yum'],
            'dnf': ['dnf'],
            'zypper': ['zypper'],
            'pacman': ['pacman']
        }

        for pm, commands in package_managers.items():
            for cmd in commands:
                if self._command_exists(cmd):
                    self.package_manager = pm
                    return pm

        return None

    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists in the system."""
        try:
            result = subprocess.run(['which', cmd], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def check_service_status(self, service_name: str) -> Dict[str, Any]:
        """Check the status of a system service."""
        service_info = {
            'name': service_name,
            'installed': False,
            'running': False,
            'enabled': False
        }

        try:
            # Check if service is installed
            result = subprocess.run(['systemctl', 'list-units', '--type=service', '--all', f'{service_name}.service'], 
                                  capture_output=True, text=True)
            service_info['installed'] = f'{service_name}.service' in result.stdout

            if service_info['installed']:
                # Check if service is active (running)
                result = subprocess.run(['systemctl', 'is-active', f'{service_name}'], 
                                      capture_output=True, text=True)
                service_info['running'] = result.stdout.strip() == 'active'

                # Check if service is enabled (starts automatically)
                result = subprocess.run(['systemctl', 'is-enabled', f'{service_name}'], 
                                      capture_output=True, text=True)
                service_info['enabled'] = result.stdout.strip() in ['enabled', 'enabled-runtime']

        except Exception as e:
            print(f"Error checking service {service_name}: {e}")

        return service_info

    def check_postfix_status(self) -> Dict[str, Any]:
        """Specifically check Postfix status."""
        return self.check_service_status('postfix')

    def check_network_connectivity(self) -> bool:
        """Check if we have network connectivity."""
        try:
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def check_sudo_privileges(self) -> bool:
        """Check if the current user has sudo privileges."""
        try:
            result = subprocess.run(['sudo', '-n', 'whoami'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        return {
            'os_info': self.detect_os(),
            'package_manager': self.detect_package_manager(),
            'postfix_status': self.check_postfix_status(),
            'has_sudo': self.check_sudo_privileges(),
            'network_connected': self.check_network_connectivity()
        }


# Example usage
if __name__ == "__main__":
    detector = SystemDetector()
    info = detector.get_system_info()
    
    print("System Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")