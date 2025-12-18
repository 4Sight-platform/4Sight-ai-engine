#!/usr/bin/env python3
"""
GSC Authentication Script
Handles OAuth flow and stores refresh token for ongoing access
"""

import sys
from src.auth import GSCAuthenticator
from src.storage import TokenStorage, PropertyStorage
from src.client import GSCClient
from src.utils import (
    print_header, print_step, print_success, print_error,
    print_warning, print_info, get_user_input, get_user_choice,
    confirm_action
)

def main():
    """Main authentication flow"""
    
    print_header("Google Search Console - Authentication Setup")
    
    # Default session ID
    session_id = "user_session"
    
    # Initialize storage
    token_storage = TokenStorage()
    property_storage = PropertyStorage()
    
    # Check if already authenticated
    if token_storage.session_exists(session_id):
        print_warning("Existing authentication found!")
        if not confirm_action("Do you want to re-authenticate (this will overwrite existing tokens)?"):
            print_info("Authentication cancelled. Using existing credentials.")
            return
        
        # Delete existing tokens
        token_storage.delete_tokens(session_id)
        property_storage.delete_property(session_id)
        print_success("Existing credentials cleared")
        print()
    
    # Step 1: Load credentials
    print_step(1, 5, "Loading OAuth credentials...")
    
    try:
        authenticator = GSCAuthenticator()
        print_success("CLIENT_ID loaded")
        print_success("CLIENT_SECRET loaded")
    except Exception as e:
        print_error(f"Failed to load credentials: {str(e)}")
        print()
        print_info("Make sure you've configured config/credentials.json with your OAuth credentials")
        sys.exit(1)
    
    # Step 2: Generate authorization URL
    print()
    print_step(2, 5, "Generating authorization URL...")
    
    try:
        auth_url = authenticator.generate_auth_url()
        print_success("Authorization URL generated")
    except Exception as e:
        print_error(f"Failed to generate URL: {str(e)}")
        sys.exit(1)
    
    # Step 3: User authorizes
    print()
    print_step(3, 5, "Authorize this application")
    print()
    print_info("Open this URL in your browser:")
    print()
    print(f"    {auth_url}")
    print()
    print_info("After authorizing, you will receive an authorization code.")
    print()
    
    auth_code = get_user_input("Paste the authorization code here")
    
    if not auth_code:
        print_error("No authorization code provided")
        sys.exit(1)
    
    # Step 4: Exchange code for tokens
    print()
    print_step(4, 5, "Exchanging authorization code for tokens...")
    
    try:
        tokens = authenticator.exchange_code(auth_code)
        print_success("Access token received")
        print_success("Refresh token received")
        
        # Save tokens
        token_path = token_storage.save_tokens(session_id, tokens)
        print_success(f"Credentials saved to: {token_path}")
    except Exception as e:
        print_error(f"Failed to exchange code: {str(e)}")
        print()
        print_info("Common issues:")
        print_info("  - Authorization code already used (they expire after one use)")
        print_info("  - Authorization code expired (valid for ~10 minutes)")
        print_info("  - Incorrect CLIENT_ID or CLIENT_SECRET")
        sys.exit(1)
    
    # Step 5: Fetch and select GSC property
    print()
    print_step(5, 5, "Fetching your GSC properties...")
    
    try:
        # Build credentials and client
        credentials = authenticator.build_credentials(
            tokens['access_token'],
            tokens['refresh_token']
        )
        client = GSCClient(credentials)
        
        # Get properties
        properties = client.list_properties()
        
        if not properties:
            print_warning("No GSC properties found for this account")
            print_info("Make sure you have at least one verified property in Search Console")
            sys.exit(1)
        
        print_success(f"Found {len(properties)} propert{'y' if len(properties) == 1 else 'ies'}")
        print()
        
        # Let user select property
        if len(properties) == 1:
            selected_property = properties[0]
            print_info(f"Auto-selected: {selected_property}")
        else:
            print_info("Select which property to analyze:")
            selected_index = get_user_choice(properties)
            selected_property = properties[selected_index]
        
        # Save selected property
        property_path = property_storage.save_property(session_id, selected_property)
        print()
        print_success(f"Property selected: {selected_property}")
        print_success(f"Configuration saved to: {property_path}")
        
    except Exception as e:
        print_error(f"Failed to fetch properties: {str(e)}")
        sys.exit(1)
    
    # Success!
    print()
    print_header("Setup Complete!")
    print()
    print_success("Google Search Console is now connected")
    print_success(f"Property: {selected_property}")
    print()
    print_info("You can now query keyword performance with:")
    print_info("  python gsc_query.py")
    print()

if __name__ == "__main__":
    main()