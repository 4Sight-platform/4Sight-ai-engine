"""
OAuth Manager for Google OAuth 2.0 Flow
Handles authorization, token exchange, and encrypted storage of refresh tokens.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from urllib.parse import urlencode
import httpx
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)


class OAuthManager:
    """
    Manages Google OAuth 2.0 flow for GSC and GA4 access.
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
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        encryption_key: Optional[str] = None
    ):
        """Initialize OAuth manager with credentials."""
        # Load from environment if not provided
        self.client_id = client_id or os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8001/api/v1/oauth/callback")
        
        # Encryption setup
        encryption_key = encryption_key or os.getenv("ENCRYPTION_KEY")
        
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
            "prompt": "consent select_account"  # Force consent and account selection
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
        Encrypt and store refresh token for the user in DATABASE.
        Access token is NOT stored (returned directly to frontend for immediate use).
        
        Args:
            user_id: User identifier
            token_data: Token data from Google (access_token, refresh_token, etc.)
        """
        refresh_token = token_data.get("refresh_token")
        
        if not refresh_token:
            logger.warning("[OAuth] No refresh_token in response. User may have already authorized.")
            # This can happen if user already granted access before
            # We don't overwrite existing token if not provided
            return
        
        # Encrypt refresh token
        encrypted_refresh = self.cipher.encrypt(refresh_token.encode()).decode()
        
        try:
            from Database.database import get_db
            from Database.models import OAuthToken
            
            db = next(get_db())
            
            # Check existing
            existing = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()
            
            if existing:
                existing.encrypted_refresh_token = encrypted_refresh
                existing.last_refreshed_at = datetime.utcnow()
                logger.info(f"[OAuth] Updated existing token for user: {user_id}")
            else:
                new_token = OAuthToken(
                    user_id=user_id,
                    encrypted_refresh_token=encrypted_refresh,
                    provider='google',
                    token_created_at=datetime.utcnow(),
                    last_refreshed_at=datetime.utcnow()
                )
                db.add(new_token)
                logger.info(f"[OAuth] Stored new token for user: {user_id}")
            
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"[OAuth] Failed to store token in DB: {e}")
            raise e
    
    def get_refresh_token(self, user_id: str) -> Optional[str]:
        """
        Retrieve and decrypt refresh token for a user from DATABASE.
        
        Args:
            user_id: User identifier
            
        Returns:
            Decrypted refresh token or None
        """
        try:
            from Database.database import get_db
            from Database.models import OAuthToken
            
            db = next(get_db())
            token_record = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()
            
            if not token_record:
                db.close()
                return None
            
            encrypted_token = token_record.encrypted_refresh_token
            db.close()
            
            if not encrypted_token:
                return None
            
            decrypted = self.cipher.decrypt(encrypted_token.encode()).decode()
            
            # Update last_refreshed_at (best effort)
            try:
                db = next(get_db())
                token = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).first()
                if token:
                    token.last_refreshed_at = datetime.utcnow()
                    db.commit()
                db.close()
            except:
                pass
                
            return decrypted
            
        except Exception as e:
            logger.error(f"[OAuth] Failed to retrieve/decrypt token: {e}")
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
    
    async def get_fresh_access_token(self, user_id: str) -> Dict[str, str]:
        """
        Get a fresh access token for the user.
        Wrapper around refresh_access_token to match expected interface.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with access_token or empty if failed
        """
        token = await self.refresh_access_token(user_id)
        if token:
            return {"access_token": token}
        return {}

    def has_valid_credentials(self, user_id: str) -> bool:
        """
        Check if user has stored credentials in DATABASE.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user has refresh token stored
        """
        try:
            from Database.database import get_db
            from Database.models import OAuthToken
            
            db = next(get_db())
            exists = db.query(OAuthToken).filter(OAuthToken.user_id == user_id).count() > 0
            db.close()
            return exists
        except Exception as e:
            logger.error(f"[OAuth] DB check failed: {e}")
            return False
    
    def revoke_tokens(self, user_id: str) -> None:
        """
        Remove stored credentials for a user from DATABASE.
        
        Args:
            user_id: User identifier
        """
        try:
            from Database.database import get_db
            from Database.models import OAuthToken
            
            db = next(get_db())
            db.query(OAuthToken).filter(OAuthToken.user_id == user_id).delete()
            db.commit()
            db.close()
            logger.info(f"[OAuth] Revoked credentials for user: {user_id}")
        except Exception as e:
            logger.error(f"[OAuth] Failed to revoke token: {e}")
    
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
