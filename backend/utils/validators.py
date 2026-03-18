"""
Validation Utilities
"""
import re


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> dict:
    """
    Validate password strength

    Returns dict with 'valid' and 'message' keys
    """
    if not password:
        return {'valid': False, 'message': 'Password is required'}

    if len(password) < 6:
        return {'valid': False, 'message': 'Password must be at least 6 characters'}

    if len(password) > 128:
        return {'valid': False, 'message': 'Password must be less than 128 characters'}

    return {'valid': True, 'message': 'Password is valid'}


def validate_username(username: str) -> dict:
    """
    Validate username

    Returns dict with 'valid' and 'message' keys
    """
    if not username:
        return {'valid': False, 'message': 'Username is required'}

    if len(username) < 3:
        return {'valid': False, 'message': 'Username must be at least 3 characters'}

    if len(username) > 80:
        return {'valid': False, 'message': 'Username must be less than 80 characters'}

    # Allow alphanumeric, underscore, and hyphen
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, username):
        return {'valid': False, 'message': 'Username can only contain letters, numbers, underscores, and hyphens'}

    return {'valid': True, 'message': 'Username is valid'}


def validate_cron_expression(expression: str) -> dict:
    """
    Validate cron expression

    Returns dict with 'valid' and 'message' keys
    """
    if not expression:
        return {'valid': False, 'message': 'Cron expression is required'}

    parts = expression.strip().split()

    if len(parts) < 5 or len(parts) > 6:
        return {'valid': False, 'message': 'Cron expression must have 5 or 6 parts'}

    # Basic validation of each part
    valid_chars = set('0123456789*,-/')

    for part in parts:
        if not all(c in valid_chars for c in part):
            return {'valid': False, 'message': 'Cron expression contains invalid characters'}

    return {'valid': True, 'message': 'Cron expression is valid'}