#!/usr/bin/env python3
"""
Installation wizard providing a step-by-step interface for SMTP relay setup.
Both CLI and web UI friendly for guided installation.
"""
import os
import sys
import json
from typing import Dict, Any, Optional, List
from installer import Installer
from system_detector import SystemDetector
import logging


class InstallationWizard:
    """Provides a step-by-step wizard for SMTP relay installation."""

    def __init__(self):
        self.installer = Installer()
        self.detector = SystemDetector()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Email provider presets
        self.provider_presets = {
            "gmail": {
                "name": "Gmail",
                "relay_host": "smtp.gmail.com",
                "relay_port": 587,
                "description": "Using Gmail SMTP requires an App Password (not regular password)",
                "help_url": "https://support.google.com/accounts/answer/185833"
            },
            "outlook": {
                "name": "Outlook/Hotmail",
                "relay_host": "smtp-mail.outlook.com",
                "relay_port": 587,
                "description": "Microsoft account with SMTP access enabled"
            },
            "sendgrid": {
                "name": "SendGrid",
                "relay_host": "smtp.sendgrid.net",
                "relay_port": 587,
                "description": "Requires SendGrid API credentials"
            },
            "aws_ses": {
                "name": "AWS SES",
                "relay_host": "email-smtp.us-east-1.amazonaws.com",  # Default region
                "relay_port": 587,
                "description": "AWS SES SMTP credentials (region-specific endpoint)"
            },
            "custom": {
                "name": "Custom SMTP",
                "relay_host": "",
                "relay_port": 587,
                "description": "Use custom SMTP server settings"
            }
        }

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for the installation."""
        return self.detector.get_system_info()

    def get_provider_presets(self) -> List[Dict[str, Any]]:
        """Get available provider presets."""
        return [
            {"key": key, "name": data["name"], "description": data["description"]}
            for key, data in self.provider_presets.items()
        ]

    def validate_input(self, input_type: str, value: str) -> Dict[str, Any]:
        """Validate user input based on type."""
        result = {"valid": True, "message": ""}
        
        if input_type == "email":
            # Basic email validation
            if "@" not in value or "." not in value.split("@")[1]:
                result["valid"] = False
                result["message"] = "Please enter a valid email address"
        elif input_type == "hostname":
            # Basic hostname validation
            if not value or len(value) < 3 or "." not in value:
                result["valid"] = False
                result["message"] = "Please enter a valid hostname"
        elif input_type == "port":
            # Port validation
            try:
                port = int(value)
                if port < 1 or port > 65535:
                    result["valid"] = False
                    result["message"] = "Port must be between 1 and 65535"
            except ValueError:
                result["valid"] = False
                result["message"] = "Port must be a number"
        elif input_type == "password":
            # Basic password validation
            if len(value) < 1:
                result["valid"] = False
                result["message"] = "Password cannot be empty"
        
        return result

    def get_provider_config(self, provider_key: str, custom_relay_host: str = None, 
                           custom_relay_port: int = None) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        if provider_key not in self.provider_presets:
            return None
        
        provider = self.provider_presets[provider_key]
        
        config = {
            "relay_host": provider["relay_host"],
            "relay_port": provider["relay_port"],
            "provider_name": provider["name"],
            "description": provider["description"]
        }
        
        # Override with custom values if provided (for custom provider)
        if provider_key == "custom" and custom_relay_host:
            config["relay_host"] = custom_relay_host
        if provider_key == "custom" and custom_relay_port:
            config["relay_port"] = custom_relay_port
        
        return config

    def run_wizard(self) -> bool:
        """Run the installation wizard in CLI mode."""
        print("=== SMTP Relay Auto-Installation Wizard ===\n")
        
        # Step 1: System check
        print("Step 1: Checking system compatibility...")
        system_info = self.get_system_info()
        
        print(f"  OS: {system_info['os_info']['name']} {system_info['os_info']['version']}")
        print(f"  Package Manager: {system_info['package_manager']}")
        print(f"  Sudo Access: {'Yes' if system_info['has_sudo'] else 'No'}")
        print(f"  Network Connected: {'Yes' if system_info['network_connected'] else 'No'}")
        
        if not system_info['has_sudo']:
            print("\nERROR: This installation requires sudo privileges.")
            return False
        
        print("\nSystem check completed successfully!\n")
        
        # Step 2: Choose provider
        print("Step 2: Choose your email provider")
        print("Available providers:")
        for i, preset in enumerate(self.get_provider_presets(), 1):
            print(f"  {i}. {preset['name']} - {preset['description']}")
        
        while True:
            try:
                choice = input("\nEnter your choice (1-5): ").strip()
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(self.get_provider_presets()):
                    selected_preset = self.get_provider_presets()[choice_idx]
                    provider_key = [k for k, v in self.provider_presets.items() if v['name'] == selected_preset['name']][0]
                    break
                else:
                    print("Invalid choice. Please enter a number between 1 and 5.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        print(f"\nSelected: {selected_preset['name']}")
        
        # Step 3: Get provider-specific settings
        if provider_key == "custom":
            print("\nStep 3: Enter custom SMTP settings")
            while True:
                custom_host = input("SMTP Server Host: ").strip()
                validation = self.validate_input("hostname", custom_host)
                if validation["valid"]:
                    break
                print(f"Error: {validation['message']}")
            
            while True:
                custom_port = input("SMTP Server Port (default 587): ").strip() or "587"
                validation = self.validate_input("port", custom_port)
                if validation["valid"]:
                    custom_port = int(custom_port)
                    break
                print(f"Error: {validation['message']}")
            
            provider_config = self.get_provider_config(provider_key, custom_host, custom_port)
        else:
            provider_config = self.get_provider_config(provider_key)
            print(f"\nUsing {provider_config['provider_name']} settings:")
            print(f"  Host: {provider_config['relay_host']}")
            print(f"  Port: {provider_config['relay_port']}")
        
        # Step 4: Get credentials
        print(f"\nStep 4: Enter your {provider_config['provider_name']} credentials")
        
        if provider_key == "gmail":
            print("  Note: For Gmail, use an App Password, not your regular password")
            print("  Learn more: https://support.google.com/accounts/answer/185833")
        
        while True:
            username = input("Username/Email: ").strip()
            validation = self.validate_input("email", username)
            if validation["valid"]:
                break
            print(f"Error: {validation['message']}")
        
        while True:
            password = input("Password/App Password: ").strip()
            validation = self.validate_input("password", password)
            if validation["valid"]:
                break
            print(f"Error: {validation['message']}")
        
        # Step 5: Confirm and install
        print(f"\nSummary:")
        print(f"  Provider: {provider_config['provider_name']}")
        print(f"  Server: {provider_config['relay_host']}:{provider_config['relay_port']}")
        print(f"  Username: {username}")
        print(f"  Password: {'*' * len(password)}")
        
        confirm = input(f"\nProceed with installation? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Installation canceled.")
            return False
        
        # Step 6: Run installation
        print("\nStarting installation...")
        success = self.installer.run_installation(
            relay_host=provider_config['relay_host'],
            relay_port=provider_config['relay_port'],
            username=username,
            password=password
        )
        
        if success:
            print("\n🎉 Installation completed successfully!")
            print("Your SMTP relay is now configured and running.")
        else:
            print("\n❌ Installation failed. Check logs for details.")
        
        return success

    def run_wizard_web(self) -> Dict[str, Any]:
        """Get wizard data for web interface."""
        return {
            "system_info": self.get_system_info(),
            "providers": self.get_provider_presets(),
            "current_step": 1,
            "total_steps": 5
        }

    def get_wizard_step(self, step_number: int) -> Dict[str, Any]:
        """Get data for a specific wizard step."""
        if step_number == 1:
            return {
                "step": 1,
                "title": "System Check",
                "system_info": self.get_system_info()
            }
        elif step_number == 2:
            return {
                "step": 2,
                "title": "Choose Email Provider",
                "providers": self.get_provider_presets()
            }
        elif step_number == 3:
            return {
                "step": 3,
                "title": "Enter SMTP Settings",
                "help_text": "Enter your custom SMTP server settings"
            }
        elif step_number == 4:
            return {
                "step": 4,
                "title": "Enter Credentials",
                "help_text": "Enter your email account credentials"
            }
        elif step_number == 5:
            return {
                "step": 5,
                "title": "Confirmation",
                "help_text": "Review your settings before installation"
            }
        else:
            return {
                "step": 0,
                "title": "Invalid Step",
                "error": "Invalid step number"
            }

    def install_with_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Install with provided configuration data."""
        try:
            success = self.installer.run_installation(
                relay_host=config.get("relay_host", ""),
                relay_port=config.get("relay_port", 587),
                username=config.get("username", ""),
                password=config.get("password", "")
            )
            
            return {
                "success": success,
                "message": "Installation completed successfully!" if success else "Installation failed. Check logs for details.",
                "installation_status": self.installer.get_installation_status()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Installation failed with error: {str(e)}",
                "installation_status": {}
            }

    def uninstall(self) -> Dict[str, Any]:
        """Run the uninstallation process."""
        try:
            success = self.installer.run_uninstallation()
            
            return {
                "success": success,
                "message": "Uninstallation completed successfully!" if success else "Uninstallation failed. Check logs for details."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Uninstallation failed with error: {str(e)}"
            }


# Example usage
if __name__ == "__main__":
    wizard = InstallationWizard()
    
    # Run the wizard in CLI mode
    if len(sys.argv) > 1 and sys.argv[1] == "--web":
        # For web interface
        wizard_data = wizard.run_wizard_web()
        print(json.dumps(wizard_data, indent=2, default=str))
    else:
        # For CLI mode
        wizard.run_wizard()