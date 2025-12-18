"""
Input Validators
Validation functions for onboarding inputs
"""

import re
from typing import Optional, List
from urllib.parse import urlparse


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_url(url: str, require_https: bool = False) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        require_https: If True, only accept https URLs
    
    Returns:
        True if valid
    
    Raises:
        ValidationError if invalid
    """
    if not url:
        raise ValidationError("URL cannot be empty")
    
    try:
        result = urlparse(url)
        
        # Check if scheme and netloc exist
        if not all([result.scheme, result.netloc]):
            raise ValidationError("Invalid URL format. Must include http:// or https://")
        
        # Check if scheme is http or https
        if result.scheme not in ['http', 'https']:
            raise ValidationError("URL must start with http:// or https://")
        
        # Optionally require HTTPS
        if require_https and result.scheme != 'https':
            raise ValidationError("URL must use HTTPS")
        
        return True
    
    except Exception as e:
        raise ValidationError(f"Invalid URL: {str(e)}")


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid
    
    Raises:
        ValidationError if invalid
    """
    if not email:
        raise ValidationError("Email cannot be empty")
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format")
    
    return True


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid
    
    Raises:
        ValidationError if invalid
    """
    if not phone:
        raise ValidationError("Phone number cannot be empty")
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    # Check if it's all digits (with optional + prefix)
    if not re.match(r'^\+?\d{10,15}$', cleaned):
        raise ValidationError("Invalid phone number format. Must be 10-15 digits.")
    
    return True


def validate_business_name(name: str) -> bool:
    """
    Validate business name
    
    Args:
        name: Business name
    
    Returns:
        True if valid
    
    Raises:
        ValidationError if invalid
    """
    if not name or not name.strip():
        raise ValidationError("Business name cannot be empty")
    
    if len(name.strip()) < 2:
        raise ValidationError("Business name must be at least 2 characters")
    
    if len(name) > 100:
        raise ValidationError("Business name must be less than 100 characters")
    
    return True


def validate_text_length(text: str, min_length: int, max_length: int, field_name: str = "Text") -> bool:
    """
    Validate text length
    
    Args:
        text: Text to validate
        min_length: Minimum length
        max_length: Maximum length
        field_name: Name of field (for error messages)
    
    Returns:
        True if valid
    
    Raises:
        ValidationError if invalid
    """
    if not text or not text.strip():
        raise ValidationError(f"{field_name} cannot be empty")
    
    length = len(text.strip())
    
    if length < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")
    
    if length > max_length:
        raise ValidationError(f"{field_name} must be less than {max_length} characters")
    
    return True


def validate_choice(choice: str, valid_choices: List[str], field_name: str = "Choice") -> bool:
    """
    Validate that choice is in valid options
    
    Args:
        choice: User's choice
        valid_choices: List of valid options
        field_name: Name of field (for error messages)
    
    Returns:
        True if valid
    
    Raises:
        ValidationError if invalid
    """
    if choice not in valid_choices:
        raise ValidationError(f"Invalid {field_name}. Must be one of: {', '.join(valid_choices)}")
    
    return True


def validate_list_not_empty(items: List, field_name: str = "List", min_items: int = 1) -> bool:
    """
    Validate that list is not empty
    
    Args:
        items: List to validate
        field_name: Name of field (for error messages)
        min_items: Minimum number of items required
    
    Returns:
        True if valid
    
    Raises:
        ValidationError if invalid
    """
    if not items or len(items) < min_items:
        raise ValidationError(f"{field_name} must have at least {min_items} item(s)")
    
    return True


def validate_keyword(keyword: str) -> bool:
    """
    Validate keyword format
    
    Args:
        keyword: Keyword to validate
    
    Returns:
        True if valid
    
    Raises:
        ValidationError if invalid
    """
    if not keyword or not keyword.strip():
        raise ValidationError("Keyword cannot be empty")
    
    # Keywords should be 2-50 characters
    if len(keyword.strip()) < 2:
        raise ValidationError("Keyword must be at least 2 characters")
    
    if len(keyword) > 50:
        raise ValidationError("Keyword must be less than 50 characters")
    
    # Keywords shouldn't have special characters except spaces and hyphens
    if not re.match(r'^[a-zA-Z0-9\s\-]+$', keyword):
        raise ValidationError("Keyword can only contain letters, numbers, spaces, and hyphens")
    
    return True


def sanitize_input(text: str) -> str:
    """
    Sanitize user input
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text


def validate_hex_color(color: str) -> bool:
    """
    Validate hex color code
    
    Args:
        color: Hex color code (e.g., #14B8A6)
    
    Returns:
        True if valid
    
    Raises:
        ValidationError if invalid
    """
    if not color:
        raise ValidationError("Color cannot be empty")
    
    if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
        raise ValidationError("Invalid color format. Must be hex code like #14B8A6")
    
    return True


# Helper function to validate and sanitize
def validate_and_sanitize(text: str, min_length: int, max_length: int, field_name: str = "Input") -> str:
    """
    Validate and sanitize text input
    
    Args:
        text: Text to validate
        min_length: Minimum length
        max_length: Maximum length
        field_name: Field name for error messages
    
    Returns:
        Sanitized text
    
    Raises:
        ValidationError if invalid
    """
    sanitized = sanitize_input(text)
    validate_text_length(sanitized, min_length, max_length, field_name)
    return sanitized    