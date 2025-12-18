"""
Token and Property Storage
Handles file-based storage for refresh tokens and GSC properties
"""

import os
import json
from datetime import datetime

class TokenStorage:
    """Handles storage and retrieval of OAuth tokens"""
    
    def __init__(self, storage_dir="storage/tokens"):
        self.storage_dir = storage_dir
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Create storage directory if it doesn't exist"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def _get_token_path(self, session_id):
        """Get the file path for a session's tokens"""
        return os.path.join(self.storage_dir, f"{session_id}.json")
    
    def save_tokens(self, session_id, tokens):
        """
        Save tokens to file
        
        Args:
            session_id: Unique identifier for the session
            tokens: Dict containing access_token, refresh_token, etc.
        """
        token_data = {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "token_expiry": tokens.get("token_expiry"),
            "credentials_json": tokens.get("credentials_json"),  # Store full credentials
            "created_at": datetime.now().isoformat()
        }
        
        filepath = self._get_token_path(session_id)
        with open(filepath, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        return filepath
    
    def load_tokens(self, session_id):
        """
        Load tokens from file
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            dict: Token data or None if not found
        """
        filepath = self._get_token_path(session_id)
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def delete_tokens(self, session_id):
        """
        Delete stored tokens
        
        Args:
            session_id: Unique identifier for the session
        """
        filepath = self._get_token_path(session_id)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def session_exists(self, session_id):
        """
        Check if a session has stored tokens
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            bool: True if session exists
        """
        filepath = self._get_token_path(session_id)
        return os.path.exists(filepath)


class PropertyStorage:
    """Handles storage and retrieval of selected GSC properties"""
    
    def __init__(self, storage_dir="storage/properties"):
        self.storage_dir = storage_dir
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Create storage directory if it doesn't exist"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def _get_property_path(self, session_id):
        """Get the file path for a session's property"""
        return os.path.join(self.storage_dir, f"{session_id}.json")
    
    def save_property(self, session_id, site_url):
        """
        Save selected GSC property to file
        
        Args:
            session_id: Unique identifier for the session
            site_url: The GSC property URL
        """
        property_data = {
            "site_url": site_url,
            "selected_at": datetime.now().isoformat()
        }
        
        filepath = self._get_property_path(session_id)
        with open(filepath, 'w') as f:
            json.dump(property_data, f, indent=2)
        
        return filepath
    
    def load_property(self, session_id):
        """
        Load selected property from file
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            str: Property URL or None if not found
        """
        filepath = self._get_property_path(session_id)
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data.get("site_url")
    
    def delete_property(self, session_id):
        """
        Delete stored property
        
        Args:
            session_id: Unique identifier for the session
        """
        filepath = self._get_property_path(session_id)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    def property_exists(self, session_id):
        """
        Check if a session has a stored property
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            bool: True if property exists
        """
        filepath = self._get_property_path(session_id)
        return os.path.exists(filepath)