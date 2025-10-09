#!/usr/bin/env python3
"""
Module for managing system services like Postfix.
Handles starting, stopping, enabling, disabling services.
"""
import subprocess
import logging
import os
from typing import Dict, Any, Optional
from system_detector import SystemDetector


class ServiceManager:
    """Manages system services like Postfix."""

    def __init__(self):
        self.detector = SystemDetector()
        self.system_info = self.detector.get_system_info()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def _run_command(self, command: list, sudo: bool = True) -> bool:
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

    def start_service(self, service_name: str) -> bool:
        """Start a system service."""
        return self._run_command(['systemctl', 'start', service_name])

    def stop_service(self, service_name: str) -> bool:
        """Stop a system service."""
        return self._run_command(['systemctl', 'stop', service_name])

    def restart_service(self, service_name: str) -> bool:
        """Restart a system service."""
        return self._run_command(['systemctl', 'restart', service_name])

    def enable_service(self, service_name: str) -> bool:
        """Enable a system service to start at boot."""
        return self._run_command(['systemctl', 'enable', service_name])

    def disable_service(self, service_name: str) -> bool:
        """Disable a system service from starting at boot."""
        return self._run_command(['systemctl', 'disable', service_name])

    def is_service_active(self, service_name: str) -> bool:
        """Check if a service is currently running/active."""
        try:
            result = subprocess.run(['systemctl', 'is-active', service_name], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip() == 'active'
        except subprocess.CalledProcessError:
            return False

    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a service is enabled to start at boot."""
        try:
            result = subprocess.run(['systemctl', 'is-enabled', service_name], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip() in ['enabled', 'enabled-runtime']
        except subprocess.CalledProcessError:
            return False

    def start_postfix(self) -> bool:
        """Start Postfix service."""
        if self.is_service_active('postfix'):
            self.logger.info("Postfix is already running")
            return True
        result = self.start_service('postfix')
        if result:
            self.logger.info("Postfix service started")
        else:
            self.logger.error("Failed to start Postfix service")
        return result

    def stop_postfix(self) -> bool:
        """Stop Postfix service."""
        if not self.is_service_active('postfix'):
            self.logger.info("Postfix is already stopped")
            return True
        result = self.stop_service('postfix')
        if result:
            self.logger.info("Postfix service stopped")
        else:
            self.logger.error("Failed to stop Postfix service")
        return result

    def restart_postfix(self) -> bool:
        """Restart Postfix service."""
        result = self.restart_service('postfix')
        if result:
            self.logger.info("Postfix service restarted")
        else:
            self.logger.error("Failed to restart Postfix service")
        return result

    def enable_postfix(self) -> bool:
        """Enable Postfix to start at boot."""
        if self.is_service_enabled('postfix'):
            self.logger.info("Postfix is already enabled at boot")
            return True
        result = self.enable_service('postfix')
        if result:
            self.logger.info("Postfix service enabled at boot")
        else:
            self.logger.error("Failed to enable Postfix service at boot")
        return result

    def disable_postfix(self) -> bool:
        """Disable Postfix from starting at boot."""
        if not self.is_service_enabled('postfix'):
            self.logger.info("Postfix is already disabled at boot")
            return True
        result = self.disable_service('postfix')
        if result:
            self.logger.info("Postfix service disabled from boot")
        else:
            self.logger.error("Failed to disable Postfix service from boot")
        return result

    def check_postfix_config(self) -> bool:
        """Check if Postfix configuration is valid."""
        try:
            result = subprocess.run(['sudo', 'postfix', 'check'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info("Postfix configuration is valid")
                return True
            else:
                self.logger.error(f"Postfix configuration error: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Error checking Postfix config: {e}")
            return False

    def get_postfix_status(self) -> Dict[str, Any]:
        """Get comprehensive Postfix status."""
        return {
            'active': self.is_service_active('postfix'),
            'enabled': self.is_service_enabled('postfix'),
            'config_valid': self.check_postfix_config()
        }

    def setup_postfix_basic_config(self) -> bool:
        """Set up basic Postfix configuration for relay."""
        try:
            # Backup existing main.cf if it doesn't exist
            main_cf_path = '/etc/postfix/main.cf'
            backup_path = f'{main_cf_path}.autoscript_backup'
            
            if not os.path.exists(backup_path) and os.path.exists(main_cf_path):
                self._run_command(['cp', main_cf_path, backup_path], sudo=True)
                self.logger.info(f"Backed up original {main_cf_path} to {backup_path}")
            
            # Create basic Postfix configuration
            basic_config = """# Basic SMTP Relay Configuration
smtpd_banner = $myhostname ESMTP
biff = no
append_dot_mydomain = no
readme_directory = no
compatibility_level = 2
myhostname = localhost
mydomain = localhost
myorigin = $mydomain
inet_interfaces = loopback-only
mydestination = $myhostname, localhost.$mydomain, $mydomain
local_transport = error:local delivery is disabled
mynetworks = 127.0.0.0/8, [::1]/128
mailbox_size_limit = 0
recipient_delimiter = +
inet_protocols = ipv4
"""
            
            # Write configuration to a temporary file first
            temp_config_path = '/tmp/basic_postfix_config.cf'
            with open(temp_config_path, 'w') as f:
                f.write(basic_config)
            
            # Copy to main.cf
            result = self._run_command(['cp', temp_config_path, main_cf_path], sudo=True)
            
            # Remove temporary file
            os.remove(temp_config_path)
            
            if result:
                self.logger.info("Basic Postfix configuration applied")
                
                # Reload Postfix
                return self.restart_postfix()
            else:
                self.logger.error("Failed to apply basic Postfix configuration")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting up basic Postfix config: {e}")
            return False


# Example usage
if __name__ == "__main__":
    sm = ServiceManager()
    
    print("Postfix Status:", sm.get_postfix_status())
    
    # Example: Start Postfix
    # sm.start_postfix()