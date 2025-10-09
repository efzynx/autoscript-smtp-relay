#!/usr/bin/env python3
"""
Main installer module for SMTP relay auto-installation system.
Coordinates all installation steps and provides user-friendly interface.
"""
import os
import sys
import time
import json
import subprocess
from typing import Dict, Any, Optional
from system_detector import SystemDetector
from package_manager import PackageManager
from service_manager import ServiceManager
from postfix_configurator import PostfixConfigurator
from backup_manager import BackupManager
import logging


class Installer:
    """Main installer class that coordinates the installation process."""

    def __init__(self):
        self.detector = SystemDetector()
        self.package_manager = PackageManager()
        self.service_manager = ServiceManager()
        self.postfix_configurator = PostfixConfigurator()
        self.backup_manager = BackupManager()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Installation status
        self.installation_steps = {
            'system_check': False,
            'dependencies_installed': False,
            'postfix_configured': False,
            'service_configured': False,
            'verification_completed': False
        }

    def run_system_check(self) -> bool:
        """Run initial system checks."""
        self.logger.info("Running system checks...")
        
        system_info = self.detector.get_system_info()
        
        # Check if system is supported
        supported_distros = ['ubuntu', 'debian', 'centos', 'rhel', 'fedora', 'rocky', 'almalinux']
        if system_info['os_info']['distro'] not in supported_distros:
            self.logger.warning(f"System {system_info['os_info']['distro']} may not be fully supported")
        
        # Check for sudo privileges
        if not system_info['has_sudo']:
            self.logger.error("This installation requires sudo privileges. Please run with appropriate permissions.")
            return False
        
        # Check network connectivity
        if not system_info['network_connected']:
            self.logger.warning("No network connectivity detected. Installation may fail without internet access.")
        
        # Check if Postfix is already installed
        postfix_installed = system_info['postfix_status']['installed']
        if postfix_installed:
            self.logger.info("Postfix is already installed")
        else:
            self.logger.info("Postfix is not installed, will install during setup")
        
        self.installation_steps['system_check'] = True
        return True

    def install_dependencies(self) -> bool:
        """Install required dependencies."""
        self.logger.info("Installing dependencies...")
        
        success = self.package_manager.install_smtp_relay_dependencies()
        
        if success:
            self.installation_steps['dependencies_installed'] = True
            self.logger.info("Dependencies installed successfully")
            return True
        else:
            self.logger.error("Failed to install dependencies")
            return False

    def setup_postfix_basic_config(self) -> bool:
        """Set up basic Postfix configuration."""
        self.logger.info("Setting up basic Postfix configuration...")
        
        # Create a backup before modifying
        self.backup_manager.create_backup("before_postfix_setup")
        
        success = self.service_manager.setup_postfix_basic_config()
        
        if success:
            self.installation_steps['postfix_configured'] = True
            self.logger.info("Postfix basic configuration completed")
            return True
        else:
            self.logger.error("Failed to set up Postfix configuration")
            return False

    def configure_smtp_relay(self, relay_host: str, relay_port: int, username: str, password: str) -> bool:
        """Configure SMTP relay settings."""
        self.logger.info(f"Configuring SMTP relay for {relay_host}:{relay_port}")
        
        success = self.postfix_configurator.configure_relay(relay_host, relay_port, username, password)
        
        if success:
            self.installation_steps['service_configured'] = True
            self.logger.info("SMTP relay configured successfully")
            return True
        else:
            self.logger.error("Failed to configure SMTP relay")
            return False

    def start_and_enable_services(self) -> bool:
        """Start and enable required services."""
        self.logger.info("Starting and enabling services...")
        
        # Enable and start Postfix
        if not self.service_manager.enable_postfix():
            self.logger.error("Failed to enable Postfix service")
            return False
        
        if not self.service_manager.start_postfix():
            self.logger.error("Failed to start Postfix service")
            return False
        
        # Verify service is running
        status = self.service_manager.get_postfix_status()
        if status['active'] and status['enabled']:
            self.installation_steps['verification_completed'] = True
            self.logger.info("Services started and enabled successfully")
            return True
        else:
            self.logger.error("Postfix service is not running or enabled properly")
            return False

    def verify_installation(self) -> Dict[str, Any]:
        """Verify that the installation was successful."""
        self.logger.info("Verifying installation...")
        
        verification_results = {
            'postfix_running': self.service_manager.is_service_active('postfix'),
            'postfix_enabled': self.service_manager.is_service_enabled('postfix'),
            'config_valid': self.postfix_configurator.check_config_validity(),
            'sasl_configured': os.path.exists('/etc/postfix/sasl_passwd'),
            'all_checks_passed': False
        }
        
        verification_results['all_checks_passed'] = (
            verification_results['postfix_running'] and
            verification_results['postfix_enabled'] and
            verification_results['config_valid']
        )
        
        return verification_results

    def run_installation(self, relay_host: str, relay_port: int, username: str, password: str) -> bool:
        """Run the complete installation process."""
        self.logger.info("Starting SMTP relay installation...")
        
        try:
            # Step 1: System check
            if not self.run_system_check():
                self.logger.error("System check failed, aborting installation")
                return False
            
            # Step 2: Install dependencies
            if not self.install_dependencies():
                self.logger.error("Dependency installation failed, aborting")
                return False
            
            # Step 3: Set up basic Postfix configuration
            if not self.setup_postfix_basic_config():
                self.logger.error("Postfix configuration failed, aborting")
                return False
            
            # Step 4: Configure SMTP relay
            if not self.configure_smtp_relay(relay_host, relay_port, username, password):
                self.logger.error("SMTP relay configuration failed, aborting")
                return False
            
            # Step 5: Start and enable services
            if not self.start_and_enable_services():
                self.logger.error("Service setup failed, aborting")
                return False
            
            # Step 6: Verify installation
            verification_results = self.verify_installation()
            if not verification_results['all_checks_passed']:
                self.logger.warning("Some verification checks failed, but installation may still work")
            
            self.logger.info("Installation completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Installation failed with error: {e}")
            return False

    def run_uninstallation(self) -> bool:
        """Uninstall the SMTP relay setup and restore system to original state."""
        self.logger.info("Starting uninstallation...")
        
        try:
            # Stop Postfix service
            self.service_manager.stop_postfix()
            
            # Disable Postfix service
            self.service_manager.disable_postfix()
            
            # Find most recent backup to restore from
            backups = self.backup_manager.get_available_backups()
            if backups:
                latest_backup = backups[0]
                self.logger.info(f"Restoring from backup: {latest_backup['name']}")
                
                # Restore the backup
                if self.backup_manager.restore_backup(latest_backup['name']):
                    self.logger.info("System configuration restored from backup")
                else:
                    self.logger.warning("Could not restore from backup")
            else:
                self.logger.info("No backups found to restore from")
            
            # Remove our config files if they exist
            config_files = [
                '/etc/postfix/sasl_passwd',
                '/etc/postfix/sasl_passwd.db',
                '/etc/postfix/canonical',
                '/etc/postfix/generic',
                '/etc/postfix/header_checks'
            ]
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    try:
                        subprocess.run(['sudo', 'rm', '-f', config_file], check=True)
                        self.logger.info(f"Removed {config_file}")
                    except:
                        self.logger.warning(f"Could not remove {config_file}")
            
            # Reset to default Postfix config if needed
            self.postfix_configurator.reset_to_defaults()
            
            # Reload Postfix
            self.service_manager.restart_postfix()
            
            self.logger.info("Uninstallation completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Uninstallation failed with error: {e}")
            return False

    def get_installation_status(self) -> Dict[str, Any]:
        """Get the current installation status."""
        return {
            'steps': self.installation_steps,
            'system_info': self.detector.get_system_info(),
            'verification_results': self.verify_installation()
        }


# Example usage
if __name__ == "__main__":
    installer = Installer()
    
    # Example: Run installation (uncomment to use)
    # result = installer.run_installation(
    #     relay_host="smtp.gmail.com",
    #     relay_port=587,
    #     username="user@gmail.com",
    #     password="password"
    # )
    # print("Installation result:", result)
    
    # Get installation status
    status = installer.get_installation_status()
    print("Installation Status:", json.dumps(status, indent=2, default=str))