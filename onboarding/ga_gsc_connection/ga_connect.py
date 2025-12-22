"""
Google Analytics 4 Connection Module (Onboarding Validation)

Replicated from GAPOC/backend/ga4_service.py
Focus: Account/Property Listing (No heavy reporting)
"""

import logging
from typing import List, Dict
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class GA4Connector:
    """
    Handles GA4 connection and property listing.
    """
    
    def __init__(self, access_token: str):
        # Construct credentials object with just the access token
        self.creds = Credentials(token=access_token)
    
    def list_properties(self) -> List[Dict[str, str]]:
        """
        Lists all GA4 properties the user has access to.
        Returns: List of {"property_id": id, "display_name": name, "account_name": name}
        """
        logger.info("[GA4] Fetching GA4 Account Summaries...")
        
        properties = []
        try:
            # Use REST API via discovery
            service = build('analyticsadmin', 'v1beta', credentials=self.creds)
            
            # List account summaries to get properties
            response = service.accountSummaries().list().execute()
            
            for summary in response.get('accountSummaries', []):
                account_name = summary.get('displayName', 'Unknown Account')
                for prop in summary.get('propertySummaries', []):
                    # property format is "properties/12345"
                    prop_resource = prop.get('property', '')
                    prop_id = prop_resource.split('/')[-1] if '/' in prop_resource else prop_resource
                    
                    properties.append({
                        "property_id": prop_id,
                        "display_name": prop.get('displayName', 'Unknown'),
                        "account_name": account_name,
                        "resource_name": prop_resource
                    })
            
            logger.info(f"[GA4] Found {len(properties)} properties")
            return properties
            
        except Exception as e:
            logger.error(f"[GA4] Failed to list properties: {e}")
            raise

    def list_data_streams(self, property_resource: str) -> List[Dict[str, str]]:
        """
        List data streams for a property to check URLs.
        Args:
            property_resource: Resource name like 'properties/12345'
        """
        try:
            service = build('analyticsadmin', 'v1beta', credentials=self.creds)
            response = service.properties().dataStreams().list(parent=property_resource).execute()
            
            streams = []
            for stream in response.get('dataStreams', []):
                if 'webStreamData' in stream:
                    streams.append({
                        'stream_id': stream.get('name'),
                        'display_name': stream.get('displayName'),
                        'default_uri': stream['webStreamData'].get('defaultUri')
                    })
            return streams
        except Exception as e:
            logger.error(f"[GA4] Failed to list data streams for {property_resource}: {e}")
            return []

    def validate_access(self, target_property_id: str) -> bool:
        """
        Check if the user has access to a specific Property ID.
        """
        try:
            properties = self.list_properties()
            for prop in properties:
                if prop['property_id'] == target_property_id:
                    return True
            return False
        except Exception:
            return False
