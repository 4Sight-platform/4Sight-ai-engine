"""
Utility functions for user ID generation and management
"""

import hashlib
from typing import Optional


def generate_user_id_from_email(email: str) -> str:
    """
    Generate a deterministic user ID from email address using MD5 hash.
    
    Args:
        email: User's email address
        
    Returns:
        User ID in format: user_<12_char_hash>
        
    Example:
        generate_user_id_from_email("john@example.com") -> "user_c4ca4238a0b9"
    """
    # Normalize email: lowercase and strip whitespace
    normalized_email = email.lower().strip()
    
    # Generate MD5 hash
    hash_obj = hashlib.md5(normalized_email.encode())
    hash_hex = hash_obj.hexdigest()
    
    # Take first 12 characters
    user_id = f"user_{hash_hex[:12]}"
    
    return user_id


def validate_user_id_format(user_id: str) -> bool:
    """
    Validate that a user ID follows the correct format.
    
    Args:
        user_id: User ID to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not user_id:
        return False
    
    if not user_id.startswith("user_"):
        return False
    
    # Should be user_ + 12 hex characters
    if len(user_id) != 17:  # len("user_") + 12
        return False
    
    # Check if characters after user_ are hexadecimal
    hash_part = user_id[5:]
    try:
        int(hash_part, 16)
        return True
    except ValueError:
        return False


def get_user_id_from_request(email: Optional[str], provided_user_id: Optional[str] = None) -> str:
    """
    Get or generate user ID from email or provided user ID.
    
    Args:
        email: User's email address
        provided_user_id: Optional pre-existing user ID
        
    Returns:
        User ID (generated or provided)
        
    Raises:
        ValueError: If neither email nor valid user_id is provided
    """
    if provided_user_id:
        if validate_user_id_format(provided_user_id):
            return provided_user_id
        else:
            raise ValueError(f"Invalid user_id format: {provided_user_id}")
    
    if email:
        return generate_user_id_from_email(email)
    
    raise ValueError("Either email or user_id must be provided")
