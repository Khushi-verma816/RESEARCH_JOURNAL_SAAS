
import re
from email_validator import validate_email as email_validate, EmailNotValidError


def validate_email(email):
    """Validate email address"""
    try:
        valid = email_validate(email)
        return True, valid.email
    except EmailNotValidError as e:
        return False, str(e)


def validate_password(password):
    """
    Validate password strength
    Requirements: min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


def validate_subdomain(subdomain):
    """Validate subdomain format"""
    # Subdomain must be alphanumeric and hyphens, 3-63 chars
    pattern = r'^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$'
    
    if not re.match(pattern, subdomain):
        return False, "Invalid subdomain format"
    
    # Reserved subdomains
    reserved = ['www', 'api', 'admin', 'app', 'mail', 'ftp', 'localhost', 'staging', 'dev']
    if subdomain.lower() in reserved:
        return False, "This subdomain is reserved"
    
    return True, None


def validate_phone(phone):
    """Validate phone number format"""
    # Basic international phone format
    pattern = r'^\+?[1-9]\d{1,14}$'
    
    if not re.match(pattern, phone):
        return False, "Invalid phone number format"
    
    return True, None


def validate_url(url):
    """Validate URL format"""
    pattern = r'^https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)$'
    
    if not re.match(pattern, url):
        return False, "Invalid URL format"
    
    return True, None