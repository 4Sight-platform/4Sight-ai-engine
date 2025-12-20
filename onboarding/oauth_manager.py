"""
OAuth Manager for Google Authentication
Handles token exchange, encryption, and storage
"""

import logging
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta
from urllib.parse import urlencode
import httpx
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class OAuthManager:
    """
    Manages OAuth flow for Google services (GSC + GA4)
    """
    
    # Google OAuth endpoints
    AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    
    # Combined scopes for GSC + GA4
    SCOPES = [
        "https://www.googleapis.com/auth/webmasters.readonly",  # GSC
        "https://www.googleapis.com/auth/analytics.readonly",   # GA4
        "openid",
        "email"
    ]
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, encryption_key: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        
        # Initialize encryption
        try:
            self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError("Invalid encryption key. Generate one with: Fernet.generate_key()")
        
        # Token storage path
        self.storage_dir = Path(__file__).parent / "storage" / "credentials"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.token_file = self.storage_dir / "oauth_tokens.json"
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Args:
            state: Optional CSRF protection token
            
        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",  # Request refresh token
            "prompt": "consent"  # Force consent to get refresh token
        }
        
        if state:
            params["state"] = state
        
        auth_url = f"{self.AUTH_ENDPOINT}?{urlencode(params)}"
        logger.info(f"[OAuth] Generated authorization URL")
        return auth_url
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, str]:
        """
        Exchange authorization code for access_token and refresh_token.
        
        Args:
            code: Authorization code from Google callback
            
        Returns:
            Dict with access_token, refresh_token, expires_in
        """
        logger.info("[OAuth] Exchanging authorization code for tokens...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_ENDPOINT,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code"
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            logger.info("[OAuth] ✓ Successfully exchanged code for tokens")
            return token_data
    
    def store_tokens(self, user_id: str, token_data: Dict[str, str]) -> None:
        """
        Encrypt and store refresh token for the user.
        Access token is NOT stored (returned directly to frontend for immediate use).
        
        Args:
            user_id: User identifier
            token_data: Token data from Google (access_token, refresh_token, etc.)
        """
        refresh_token = token_data.get("refresh_token")
        
        if not refresh_token:
            logger.warning("[OAuth] No refresh_token in response. User may have already authorized.")
            # This can happen if user already granted access before
            # In production, you'd want to handle this case
        
        # Encrypt refresh token
        encrypted_refresh = self.cipher.encrypt(refresh_token.encode()).decode()
        
        # Load existing storage
        storage = self._load_storage()
        
        # Store encrypted token
        storage[user_id] = {
            "encrypted_refresh_token": encrypted_refresh,
            "created_at": datetime.utcnow().isoformat(),
            "last_used_at": None
        }
        
        self._save_storage(storage)
        logger.info(f"[OAuth] ✓ Stored encrypted refresh token for user: {user_id}")
    
    def get_refresh_token(self, user_id: str) -> Optional[str]:
        """
        Retrieve and decrypt refresh token for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Decrypted refresh token or None
        """
        storage = self._load_storage()
        
        if user_id not in storage:
            return None
        
        encrypted_token = storage[user_id].get("encrypted_refresh_token")
        if not encrypted_token:
            return None
        
        try:
            decrypted = self.cipher.decrypt(encrypted_token.encode()).decode()
            
            # Update last_used_at
            storage[user_id]["last_used_at"] = datetime.utcnow().isoformat()
            self._save_storage(storage)
            
            return decrypted
        except Exception as e:
            logger.error(f"[OAuth] Failed to decrypt token: {e}")
            return None
    
    async def refresh_access_token(self, user_id: str) -> Optional[str]:
        """
        Use stored refresh token to get a new access token.
        
        Args:
            user_id: User identifier
            
        Returns:
            New access_token or None
        """
        refresh_token = self.get_refresh_token(user_id)
        
        if not refresh_token:
            logger.warning(f"[OAuth] No refresh token found for user: {user_id}")
            return None
        
        logger.info(f"[OAuth] Refreshing access token for user: {user_id}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_ENDPOINT,
                data={
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token"
                },
                timeout=30.0
            )
            
            if response.status_code == 400:
                logger.error("[OAuth] Refresh token may be invalid/revoked")
                return None
            
            response.raise_for_status()
            token_data = response.json()
            
            logger.info("[OAuth] ✓ Successfully refreshed access token")
            return token_data.get("access_token")
    
    def has_valid_credentials(self, user_id: str) -> bool:
        """
        Check if user has stored credentials.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user has refresh token stored
        """
        storage = self._load_storage()
        return user_id in storage and "encrypted_refresh_token" in storage[user_id]
    
    def revoke_tokens(self, user_id: str) -> None:
        """
        Remove stored credentials for a user.
        
        Args:
            user_id: User identifier
        """
        storage = self._load_storage()
        if user_id in storage:
            del storage[user_id]
            self._save_storage(storage)
            logger.info(f"[OAuth] Revoked credentials for user: {user_id}")
    
    # Private helper methods
    
    def _load_storage(self) -> Dict:
        """Load token storage from disk."""
        if not self.token_file.exists():
            return {}
        
        try:
            with open(self.token_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load token storage: {e}")
            return {}
    
    def _save_storage(self, storage: Dict) -> None:
        """Save token storage to disk."""
        try:
            with open(self.token_file, 'w') as f:
                json.dump(storage, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save token storage: {e}")
