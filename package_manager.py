#!/usr/bin/env python3
"""
Module for managing packages across different Linux distributions.
Handles package installation, removal, and updates for various package managers.
"""
import subprocess
import logging
from typing import List, Optional
from system_detector import SystemDetector


class PackageManager:
    """Handles package management across different Linux distributions."""

    def __init__(self):
        self.detector = SystemDetector()
        self.system_info = self.detector.get_system_info()
        self.package_manager = self.system_info['package_manager']
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def _run_command(self, command: List[str], sudo: bool = False) -> bool:
        """Run a command, optionally with sudo privileges."""
        if sudo and self.system_info['has_sudo']:
            full_command = ['sudo'] + command
        else:
            full_command = command

        try:
            self.logger.info(f"Running command: {' '.join(full_command)}")
            result = subprocess.run(full_command, capture_output=True, text=True, check=True)
            self.logger.debug(f"Command output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(full_command)} - Error: {e}")
            self.logger.error(f"Error output: {e.stderr}")
            return False

    def install_packages(self, packages: List[str], update_cache: bool = True) -> bool:
        """Install packages based on the system's package manager."""
        if not self.package_manager:
            self.logger.error("No supported package manager found!")
            return False

        # Update package cache if requested
        if update_cache:
            if not self.update_package_cache():
                self.logger.warning("Failed to update package cache, continuing...")

        # Install packages based on package manager
        if self.package_manager == 'apt':
            return self._install_packages_apt(packages)
        elif self.package_manager in ['yum', 'dnf']:
            return self._install_packages_yum_dnf(packages)
        elif self.package_manager == 'zypper':
            return self._install_packages_zypper(packages)
        elif self.package_manager == 'pacman':
            return self._install_packages_pacman(packages)
        else:
            self.logger.error(f"Unsupported package manager: {self.package_manager}")
            return False

    def _install_packages_apt(self, packages: List[str]) -> bool:
        """Install packages for APT-based systems (Debian, Ubuntu)."""
        cmd = ['apt', 'install', '-y'] + packages
        return self._run_command(cmd, sudo=True)

    def _install_packages_yum_dnf(self, packages: List[str]) -> bool:
        """Install packages for YUM/DNF-based systems (CentOS, Fedora, RHEL)."""
        if self.package_manager == 'dnf':
            cmd = ['dnf', 'install', '-y'] + packages
        else:  # yum
            cmd = ['yum', 'install', '-y'] + packages
        return self._run_command(cmd, sudo=True)

    def _install_packages_zypper(self, packages: List[str]) -> bool:
        """Install packages for Zypper-based systems (openSUSE)."""
        cmd = ['zypper', '--non-interactive', 'install'] + packages
        return self._run_command(cmd, sudo=True)

    def _install_packages_pacman(self, packages: List[str]) -> bool:
        """Install packages for Pacman-based systems (Arch Linux)."""
        cmd = ['pacman', '-S', '--noconfirm'] + packages
        return self._run_command(cmd, sudo=True)

    def update_package_cache(self) -> bool:
        """Update the package cache."""
        if not self.package_manager:
            self.logger.error("No supported package manager found!")
            return False

        if self.package_manager == 'apt':
            cmd = ['apt', 'update']
        elif self.package_manager == 'dnf':
            cmd = ['dnf', 'check-update']
        elif self.package_manager == 'yum':
            cmd = ['yum', 'check-update']
        elif self.package_manager == 'zypper':
            cmd = ['zypper', 'refresh']
        elif self.package_manager == 'pacman':
            cmd = ['pacman', '-Sy']
        else:
            self.logger.error(f"Unsupported package manager: {self.package_manager}")
            return False

        return self._run_command(cmd, sudo=True)

    def remove_packages(self, packages: List[str]) -> bool:
        """Remove packages based on the system's package manager."""
        if not self.package_manager:
            self.logger.error("No supported package manager found!")
            return False

        if self.package_manager == 'apt':
            cmd = ['apt', 'remove', '-y'] + packages
        elif self.package_manager in ['yum', 'dnf']:
            if self.package_manager == 'dnf':
                cmd = ['dnf', 'remove', '-y'] + packages
            else:  # yum
                cmd = ['yum', 'remove', '-y'] + packages
        elif self.package_manager == 'zypper':
            cmd = ['zypper', '--non-interactive', 'remove'] + packages
        elif self.package_manager == 'pacman':
            cmd = ['pacman', '-R', '--noconfirm'] + packages
        else:
            self.logger.error(f"Unsupported package manager: {self.package_manager}")
            return False

        return self._run_command(cmd, sudo=True)

    def check_package_installed(self, package_name: str) -> bool:
        """Check if a package is installed."""
        if not self.package_manager:
            return False

        try:
            if self.package_manager == 'apt':
                result = subprocess.run(['dpkg', '-l', package_name], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            elif self.package_manager in ['yum', 'dnf', 'zypper']:
                result = subprocess.run(['rpm', '-q', package_name], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            elif self.package_manager == 'pacman':
                result = subprocess.run(['pacman', '-Q', package_name], 
                                      capture_output=True, text=True)
                return result.returncode == 0
        except:
            pass
        
        return False

    def install_smtp_relay_dependencies(self) -> bool:
        """Install common SMTP relay dependencies."""
        # Determine packages based on the package manager
        if self.package_manager in ['apt']:
            packages = [
                'postfix',
                'mailutils',
                'libsasl2-modules',
                'sasl2-bin',
                'ca-certificates',
                'curl',
                'wget'
            ]
        elif self.package_manager in ['yum', 'dnf']:
            packages = [
                'postfix',
                'mailx',
                'cyrus-sasl',
                'cyrus-sasl-plain',
                'cyrus-sasl-md5',
                'ca-certificates',
                'curl',
                'wget'
            ]
        elif self.package_manager == 'zypper':
            packages = [
                'postfix',
                'mailx',
                'cyrus-sasl',
                'cyrus-sasl-plain',
                'ca-certificates',
                'curl',
                'wget'
            ]
        elif self.package_manager == 'pacman':
            packages = [
                'postfix',
                's-nail',  # mailutils equivalent for Arch
                'cyrus-sasl',
                'ca-certificates',
                'curl',
                'wget'
            ]
        else:
            self.logger.error(f"Unsupported package manager: {self.package_manager}")
            return False

        self.logger.info(f"Installing SMTP relay dependencies: {packages}")
        return self.install_packages(packages)

    def is_service_available(self, service_name: str) -> bool:
        """Check if a service is available on the system."""
        try:
            result = subprocess.run(['systemctl', 'list-units', '--type=service', '--all', f'{service_name}.service'], 
                                  capture_output=True, text=True)
            return f'{service_name}.service' in result.stdout
        except:
            return False


# Example usage
if __name__ == "__main__":
    pm = PackageManager()
    
    # Check system information
    print("Package Manager:", pm.package_manager)
    print("System Info:", pm.system_info)
    
    # Example: Install dependencies
    # pm.install_smtp_relay_dependencies()