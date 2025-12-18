"""
OAuth Authentication Handler
Manages the OAuth 2.0 flow for Google Search Console API
"""

import json
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import OAuth2Credentials
import httplib2

class GSCAuthenticator:
    """Handles OAuth authentication for GSC API"""
    
    def __init__(self, config_path="config/credentials.json"):
        self.config = self._load_config(config_path)
        self.flow = None
    
    def _load_config(self, config_path):
        """Load OAuth credentials from config file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate required fields
            required = ['client_id', 'client_secret', 'redirect_uri', 'oauth_scope']
            missing = [field for field in required if field not in config]
            
            if missing:
                raise ValueError(f"Missing required config fields: {missing}")
            
            # Check for placeholder values
            if config['client_id'] == 'YOUR_CLIENT_ID_HERE':
                raise ValueError("Please set your CLIENT_ID in config/credentials.json")
            if config['client_secret'] == 'YOUR_CLIENT_SECRET_HERE':
                raise ValueError("Please set your CLIENT_SECRET in config/credentials.json")
            
            return config
        
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in config file: {config_path}")
    
    def generate_auth_url(self):
        """
        Generate the authorization URL for user to visit
        
        Returns:
            str: Authorization URL
        """
        self.flow = OAuth2WebServerFlow(
            client_id=self.config['client_id'],
            client_secret=self.config['client_secret'],
            scope=self.config['oauth_scope'],
            redirect_uri=self.config['redirect_uri'],
            access_type='offline',
            prompt='consent'
        )
        
        auth_url = self.flow.step1_get_authorize_url()
        return auth_url
    
    def exchange_code(self, auth_code):
        """
        Exchange authorization code for access and refresh tokens
        
        Args:
            auth_code: Authorization code from OAuth callback
            
        Returns:
            dict: Contains access_token, refresh_token, token_expiry
        """
        if not self.flow:
            raise ValueError("Must call generate_auth_url() first")
        
        try:
            credentials = self.flow.step2_exchange(auth_code)
            
            return {
                "access_token": credentials.access_token,
                "refresh_token": credentials.refresh_token,
                "token_expiry": credentials.token_expiry.isoformat() if credentials.token_expiry else None,
                "credentials_json": credentials.to_json()  # Store full credentials
            }
        
        except Exception as e:
            raise ValueError(f"Failed to exchange authorization code: {str(e)}")
    
    def refresh_access_token(self, refresh_token):
        """
        Use refresh token to get a new access token
        
        Args:
            refresh_token: The stored refresh token
            
        Returns:
            str: New access token
        """
        try:
            # Build credentials from refresh token
            credentials = OAuth2Credentials(
                access_token=None,
                client_id=self.config['client_id'],
                client_secret=self.config['client_secret'],
                refresh_token=refresh_token,
                token_expiry=None,
                token_uri='https://oauth2.googleapis.com/token',
                user_agent=None
            )
            
            # Refresh the token
            http = httplib2.Http()
            credentials.refresh(http)
            
            return credentials.access_token
        
        except Exception as e:
            raise ValueError(f"Failed to refresh access token: {str(e)}")
    
    def build_credentials(self, access_token, refresh_token):
        """
        Build credentials object from tokens
        
        Args:
            access_token: Current access token
            refresh_token: Refresh token
            
        Returns:
            OAuth2Credentials: OAuth2 credentials object
        """
        credentials = OAuth2Credentials(
            access_token=access_token,
            client_id=self.config['client_id'],
            client_secret=self.config['client_secret'],
            refresh_token=refresh_token,
            token_expiry=None,
            token_uri='https://oauth2.googleapis.com/token',
            user_agent=None
        )
        
        return credentials
    
    def credentials_from_json(self, credentials_json):
        """
        Build credentials from stored JSON string
        
        Args:
            credentials_json: JSON string containing credentials
            
        Returns:
            OAuth2Credentials: OAuth2 credentials object
        """
        try:
            credentials = OAuth2Credentials.from_json(credentials_json)
            
            # Refresh if expired
            if credentials.access_token_expired:
                http = httplib2.Http()
                credentials.refresh(http)
            
            return credentials
        
        except Exception as e:
            raise ValueError(f"Failed to load credentials from JSON: {str(e)}")