#!/usr/bin/env python3
"""
Module for configuring Postfix for SMTP relay.
Handles Postfix configuration for different email providers.
"""
import os
import subprocess
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class PostfixConfigurator:
    """Configures Postfix for SMTP relay."""

    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Postfix configuration file paths
        self.main_cf_path = "/etc/postfix/main.cf"
        self.sasl_passwd_path = "/etc/postfix/sasl_passwd"
        self.canonical_path = "/etc/postfix/canonical"
        self.generic_path = "/etc/postfix/generic"

        # Known provider settings
        self.provider_configs = {
            "gmail": {
                "relay_host": "[smtp.gmail.com]:587",
                "relayhost": "[smtp.gmail.com]:587",
                "smtp_sasl_auth_enable": "yes",
                "smtp_sasl_password_maps": "hash:/etc/postfix/sasl_passwd",
                "smtp_sasl_security_options": "noanonymous",
                "smtp_tls_security_level": "encrypt",
                "smtp_sasl_tls_security_options": "noanonymous",
                "header_checks": "regexp:/etc/postfix/header_checks"
            },
            "outlook": {
                "relay_host": "[smtp-mail.outlook.com]:587",
                "relayhost": "[smtp-mail.outlook.com]:587",
                "smtp_sasl_auth_enable": "yes",
                "smtp_sasl_password_maps": "hash:/etc/postfix/sasl_passwd",
                "smtp_sasl_security_options": "noanonymous",
                "smtp_tls_security_level": "encrypt",
                "smtp_sasl_tls_security_options": "noanonymous"
            },
            "sendgrid": {
                "relay_host": "[smtp.sendgrid.net]:587",
                "relayhost": "[smtp.sendgrid.net]:587",
                "smtp_sasl_auth_enable": "yes",
                "smtp_sasl_password_maps": "hash:/etc/postfix/sasl_passwd",
                "smtp_sasl_security_options": "noanonymous",
                "smtp_tls_security_level": "encrypt",
                "smtp_sasl_tls_security_options": "noanonymous"
            },
            "aws_ses": {
                "relay_host": "[email-smtp.us-east-1.amazonaws.com]:587",  # Region-specific
                "relayhost": "[email-smtp.us-east-1.amazonaws.com]:587",  # Region-specific
                "smtp_sasl_auth_enable": "yes",
                "smtp_sasl_password_maps": "hash:/etc/postfix/sasl_passwd",
                "smtp_sasl_security_options": "noanonymous",
                "smtp_tls_security_level": "encrypt",
                "smtp_sasl_tls_security_options": "noanonymous"
            },
            "custom": {}  # Will be configured with user-provided values
        }

    def _backup_file(self, file_path: str) -> str:
        """Create a backup of a configuration file."""
        if os.path.exists(file_path):
            backup_path = f"{file_path}.autoscript_backup"
            try:
                subprocess.run(['sudo', 'cp', file_path, backup_path], check=True)
                self.logger.info(f"Backed up {file_path} to {backup_path}")
                return backup_path
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to backup {file_path}: {e}")
                return None
        return None

    def _write_config_line(self, config_file_path: str, key: str, value: str):
        """Add or update a configuration line in a Postfix file."""
        # Read the existing file
        config_content = ""
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r') as f:
                config_content = f.read()
        
        # Check if the key already exists and update it, otherwise append
        lines = config_content.split('\n')
        key_found = False
        updated_lines = []
        
        for line in lines:
            if line.strip().startswith(f"{key} = "):
                updated_lines.append(f"{key} = {value}")
                key_found = True
            else:
                updated_lines.append(line)
        
        # If key not found, append it
        if not key_found:
            updated_lines.append(f"{key} = {value}")
        
        # Write the updated content back to the file
        with open(config_file_path, 'w') as f:
            f.write('\n'.join(updated_lines))

    def configure_relay(self, relay_host: str, relay_port: int, username: str, password: str, 
                       provider: str = "custom", domain: str = None) -> bool:
        """Configure Postfix for SMTP relay."""
        try:
            self.logger.info(f"Configuring Postfix relay for {relay_host}:{relay_port}")
            
            # 1. Backup existing configuration
            self._backup_file(self.main_cf_path)
            
            # 2. Configure SASL authentication
            self._configure_sasl_auth(username, password, relay_host, relay_port)
            
            # 3. Update Postfix main configuration
            self._update_main_config(relay_host, relay_port, provider)
            
            # 4. Reload Postfix
            return self._reload_postfix()
            
        except Exception as e:
            self.logger.error(f"Error configuring Postfix relay: {e}")
            return False

    def _configure_sasl_auth(self, username: str, password: str, relay_host: str, relay_port: int):
        """Configure SASL authentication."""
        # Create SASL password file
        sasl_entry = f"[{relay_host}]:{relay_port} {username}:{password}"
        
        with open('/tmp/sasl_passwd', 'w') as f:
            f.write(sasl_entry + '\n')
        
        # Move to the correct location with proper permissions
        subprocess.run(['sudo', 'mv', '/tmp/sasl_passwd', self.sasl_passwd_path], check=True)
        subprocess.run(['sudo', 'chmod', '600', self.sasl_passwd_path], check=True)
        
        # Create the hash database
        subprocess.run(['sudo', 'postmap', self.sasl_passwd_path], check=True)
        # postmap creates sasl_passwd.db, so ensure it also has the right permissions
        subprocess.run(['sudo', 'chmod', '600', f'{self.sasl_passwd_path}.db'], check=True)
        
        self.logger.info("SASL authentication configured")

    def _update_main_config(self, relay_host: str, relay_port: int, provider: str = "custom"):
        """Update the main.cf configuration file."""
        # Get provider-specific settings or use defaults
        if provider in self.provider_configs:
            config_settings = self.provider_configs[provider]
        else:
            config_settings = self.provider_configs["custom"]
        
        # Determine the relay host string
        formatted_relayhost = f"[{relay_host}]:{relay_port}"
        
        # Get current main.cf content
        main_cf_content = ""
        if os.path.exists(self.main_cf_path):
            with open(self.main_cf_path, 'r') as f:
                main_cf_content = f.read()
        
        # Update or add the necessary configuration settings
        updated_content = self._update_postfix_config(main_cf_content, formatted_relayhost, config_settings)
        
        # Write the updated configuration to a temporary file first
        temp_main_cf = '/tmp/main.cf'
        with open(temp_main_cf, 'w') as f:
            f.write(updated_content)
        
        # Copy to the actual location
        subprocess.run(['sudo', 'cp', temp_main_cf, self.main_cf_path], check=True)
        
        # Remove temporary file
        os.remove(temp_main_cf)
        
        self.logger.info("Main configuration updated")

    def _update_postfix_config(self, current_content: str, relayhost: str, config_settings: Dict[str, str]) -> str:
        """Updates the Postfix configuration content."""
        lines = current_content.split('\n')
        updated_lines = []
        keys_added = set()
        
        for line in lines:
            # Skip lines that match keys we're going to add/update
            should_skip = False
            for key in ['relayhost', 'smtp_sasl_auth_enable', 'smtp_sasl_password_maps', 
                       'smtp_sasl_security_options', 'smtp_tls_security_level', 
                       'smtp_sasl_tls_security_options', 'inet_protocols']:
                if line.strip().startswith(f"{key} = "):
                    should_skip = True
                    break
            
            if not should_skip:
                updated_lines.append(line)
        
        # Add the configuration settings
        updated_lines.append(f"relayhost = {relayhost}")
        for key, value in config_settings.items():
            if key not in ['relay_host', 'relayhost']:  # Skip these as relayhost is already added
                if key in ['smtp_sasl_auth_enable', 'smtp_sasl_password_maps', 'smtp_sasl_security_options', 
                          'smtp_tls_security_level', 'smtp_sasl_tls_security_options', 'inet_protocols']:
                    updated_lines.append(f"{key} = {value}")
        
        # Ensure inet_protocols is set if not already present
        if not any('inet_protocols' in line for line in updated_lines):
            updated_lines.append("inet_protocols = ipv4")
        
        return '\n'.join(updated_lines)

    def _reload_postfix(self) -> bool:
        """Reload Postfix to apply configuration changes."""
        try:
            result = subprocess.run(['sudo', 'postfix', 'reload'], capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Postfix reload failed: {result.stderr}")
                # Try restart instead
                result = subprocess.run(['sudo', 'systemctl', 'restart', 'postfix'], capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"Postfix restart failed: {result.stderr}")
                    return False
                else:
                    self.logger.info("Postfix restarted successfully")
                    return True
            else:
                self.logger.info("Postfix reloaded successfully")
                return True
        except Exception as e:
            self.logger.error(f"Error reloading Postfix: {e}")
            return False

    def configure_for_provider(self, provider: str, username: str, password: str, 
                             additional_config: Optional[Dict[str, str]] = None) -> bool:
        """Configure Postfix for a specific email provider."""
        try:
            self.logger.info(f"Configuring Postfix for provider: {provider}")
            
            # Get provider-specific settings
            provider_config = self.provider_configs.get(provider, self.provider_configs["custom"])
            
            # If custom, we need the relay host from additional_config
            if provider == "custom":
                if not additional_config or 'relay_host' not in additional_config or 'relay_port' not in additional_config:
                    raise ValueError("Custom provider requires relay_host and relay_port in additional_config")
                
                return self.configure_relay(
                    relay_host=additional_config['relay_host'],
                    relay_port=additional_config.get('relay_port', 587),
                    username=username,
                    password=password,
                    provider=provider
                )
            
            # For known providers
            relay_host = provider_config["relay_host"].split(':')[0].strip('[]')
            relay_port = int(provider_config["relay_host"].split(':')[1])
            
            return self.configure_relay(relay_host, relay_port, username, password, provider)
            
        except Exception as e:
            self.logger.error(f"Error configuring Postfix for {provider}: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """Reset Postfix configuration to basic defaults."""
        try:
            self.logger.info("Resetting Postfix to default configuration")
            
            # Backup current config
            self._backup_file(self.main_cf_path)
            
            # Create basic configuration
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
            
            # Write to temp file first
            temp_config = '/tmp/main.cf'
            with open(temp_config, 'w') as f:
                f.write(basic_config)
            
            # Copy to actual location
            subprocess.run(['sudo', 'cp', temp_config, self.main_cf_path], check=True)
            os.remove(temp_config)
            
            # Remove SASL password file if it exists
            if os.path.exists(self.sasl_passwd_path):
                subprocess.run(['sudo', 'rm', '-f', self.sasl_passwd_path], check=True)
                subprocess.run(['sudo', 'rm', '-f', f'{self.sasl_passwd_path}.db'], check=True)
            
            # Reload Postfix
            return self._reload_postfix()
            
        except Exception as e:
            self.logger.error(f"Error resetting to defaults: {e}")
            return False

    def check_config_validity(self) -> bool:
        """Check if Postfix configuration is valid."""
        try:
            result = subprocess.run(['sudo', 'postfix', 'check'], capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Error checking Postfix config: {e}")
            return False


# Example usage
if __name__ == "__main__":
    pc = PostfixConfigurator()
    
    # Example: Configure for Gmail
    # pc.configure_for_provider("gmail", "user@gmail.com", "app_password")
    
    # Example: Reset to defaults
    # pc.reset_to_defaults()