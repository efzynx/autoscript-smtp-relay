#!/usr/bin/env python3
"""
Module for managing configuration backups and restoration.
Handles backing up and restoring critical files and configurations.
"""
import os
import shutil
import subprocess
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class BackupManager:
    """Manages configuration backups and restoration."""

    def __init__(self, backup_dir: str = "/tmp/smtp_relay_backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Files that need to be backed up for SMTP relay
        self.config_files = [
            '/etc/postfix/main.cf',
            '/etc/postfix/master.cf',
            '/etc/postfix/sasl_passwd',
            '/etc/postfix/sasl_passwd.db',
            '/etc/postfix/canonical',
            '/etc/postfix/generic',
            '/etc/aliases',
            '/etc/mailname'
        ]

    def create_backup(self, name: str = None) -> str:
        """Create a backup of configuration files."""
        if not name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"smtp_relay_backup_{timestamp}"
        
        backup_path = self.backup_dir / name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Creating backup: {backup_path}")
        
        # Create metadata file
        metadata_path = backup_path / "metadata.json"
        metadata = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "config_files": []
        }
        
        # Backup each configuration file
        backed_up_files = []
        for file_path in self.config_files:
            if os.path.exists(file_path):
                try:
                    # Create directory structure in backup
                    file_backup_path = backup_path / "config_files" / file_path.strip('/')
                    file_backup_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(file_path, file_backup_path)
                    backed_up_files.append(file_path)
                    self.logger.info(f"Backed up: {file_path}")
                except Exception as e:
                    self.logger.error(f"Failed to backup {file_path}: {e}")
        
        metadata["config_files"] = backed_up_files
        
        # Save sender configuration if it exists
        if os.path.exists("sender.json"):
            try:
                sender_backup_path = backup_path / "sender.json"
                shutil.copy2("sender.json", sender_backup_path)
                metadata["sender_config"] = "sender.json"
                self.logger.info("Backed up sender configuration")
            except Exception as e:
                self.logger.error(f"Failed to backup sender.json: {e}")
        
        # Save sasl configuration if it exists
        if os.path.exists("sasl_config.json"):
            try:
                sasl_backup_path = backup_path / "sasl_config.json"
                shutil.copy2("sasl_config.json", sasl_backup_path)
                metadata["sasl_config"] = "sasl_config.json"
                self.logger.info("Backed up SASL configuration")
            except Exception as e:
                self.logger.error(f"Failed to backup sasl_config.json: {e}")
        
        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Backup completed: {backup_path}")
        return str(backup_path)

    def get_available_backups(self) -> List[Dict[str, Any]]:
        """Get list of available backups."""
        backups = []
        for item in self.backup_dir.iterdir():
            if item.is_dir():
                metadata_path = item / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        backups.append({
                            "name": item.name,
                            "path": str(item),
                            "created_at": metadata.get("created_at", ""),
                            "config_files": metadata.get("config_files", [])
                        })
                    except Exception as e:
                        self.logger.error(f"Error reading metadata for {item}: {e}")
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups

    def restore_backup(self, backup_name: str) -> bool:
        """Restore a backup."""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            self.logger.error(f"Backup {backup_name} does not exist")
            return False
        
        metadata_path = backup_path / "metadata.json"
        if not metadata_path.exists():
            self.logger.error(f"Metadata not found for backup {backup_name}")
            return False
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self.logger.info(f"Restoring backup: {backup_name}")
            
            # Restore configuration files
            for file_path in metadata.get("config_files", []):
                backup_file_path = backup_path / "config_files" / file_path.strip('/')
                if backup_file_path.exists():
                    try:
                        # Create directory if it doesn't exist
                        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy file back
                        subprocess.run(['sudo', 'cp', str(backup_file_path), file_path], check=True)
                        subprocess.run(['sudo', 'chown', 'root:root', file_path], check=True)
                        subprocess.run(['sudo', 'chmod', '644', file_path], check=True)
                        
                        # Special handling for sasl_passwd.db
                        if file_path.endswith('sasl_passwd.db'):
                            subprocess.run(['sudo', 'chmod', '600', file_path], check=True)
                        
                        self.logger.info(f"Restored: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to restore {file_path}: {e}")
                        return False
            
            # Restore sender configuration if it was backed up
            if "sender_config" in metadata:
                sender_backup_path = backup_path / "sender.json"
                if sender_backup_path.exists():
                    try:
                        shutil.copy2(sender_backup_path, "sender.json")
                        self.logger.info("Restored sender configuration")
                    except Exception as e:
                        self.logger.error(f"Failed to restore sender.json: {e}")
            
            # Restore sasl configuration if it was backed up
            if "sasl_config" in metadata:
                sasl_backup_path = backup_path / "sasl_config.json"
                if sasl_backup_path.exists():
                    try:
                        shutil.copy2(sasl_backup_path, "sasl_config.json")
                        self.logger.info("Restored SASL configuration")
                    except Exception as e:
                        self.logger.error(f"Failed to restore sasl_config.json: {e}")
            
            self.logger.info(f"Backup {backup_name} restored successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring backup {backup_name}: {e}")
            return False

    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup."""
        backup_path = self.backup_dir / backup_name
        if backup_path.exists():
            try:
                shutil.rmtree(backup_path)
                self.logger.info(f"Deleted backup: {backup_name}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to delete backup {backup_name}: {e}")
                return False
        else:
            self.logger.error(f"Backup {backup_name} does not exist")
            return False

    def cleanup_old_backups(self, keep_count: int = 5) -> bool:
        """Keep only the specified number of most recent backups."""
        try:
            backups = self.get_available_backups()
            if len(backups) <= keep_count:
                return True
            
            # Get backups to delete (all but the most recent 'keep_count')
            backups_to_delete = backups[keep_count:]
            
            for backup in backups_to_delete:
                self.delete_backup(backup["name"])
            
            self.logger.info(f"Cleaned up old backups, kept {keep_count} most recent")
            return True
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")
            return False


# Example usage
if __name__ == "__main__":
    bm = BackupManager()
    
    # List available backups
    print("Available backups:")
    for backup in bm.get_available_backups():
        print(f"  - {backup['name']} ({backup['created_at']})")
    
    # Create a new backup
    # backup_name = bm.create_backup()
    # print(f"Created backup: {backup_name}")
    
    # Restore a backup (use a real backup name)
    # bm.restore_backup("smtp_relay_backup_20231201_120000")