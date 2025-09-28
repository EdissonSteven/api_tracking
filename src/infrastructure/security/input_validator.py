import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Input sanitization and validation"""
    
    # Regex patterns for validation
    TRACKING_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,50}$')
    OPERATOR_PATTERN = re.compile(r'^[A-Za-z0-9\s._-]{1,100}$')
    LOCATION_PATTERN = re.compile(r'^[A-Za-z0-9\s.,_-]{1,500}$')
    
    # Blocked patterns (basic XSS/injection prevention)
    BLOCKED_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
        re.compile(r'(union|select|insert|update|delete|drop|create|alter)\s+', re.IGNORECASE),
        re.compile(r'[<>"\'\(\);]')
    ]
    
    @classmethod
    def validate_tracking_id(cls, tracking_id: str) -> str:
        """Validate and sanitize tracking ID"""
        if not tracking_id or not isinstance(tracking_id, str):
            raise ValueError("Tracking ID is required and must be a string")
        
        tracking_id = tracking_id.strip()
        
        if not cls.TRACKING_ID_PATTERN.match(tracking_id):
            raise ValueError("Invalid tracking ID format")
        
        if cls._contains_malicious_content(tracking_id):
            raise ValueError("Tracking ID contains invalid characters")
        
        return tracking_id
    
    @classmethod
    def validate_operator(cls, operator: Optional[str]) -> Optional[str]:
        """Validate and sanitize operator field"""
        if not operator:
            return None
        
        if not isinstance(operator, str):
            raise ValueError("Operator must be a string")
        
        operator = operator.strip()
        
        if not cls.OPERATOR_PATTERN.match(operator):
            raise ValueError("Invalid operator format")
        
        if cls._contains_malicious_content(operator):
            raise ValueError("Operator contains invalid characters")
        
        return operator
    
    @classmethod
    def validate_location(cls, location: Optional[str]) -> Optional[str]:
        """Validate and sanitize location field"""
        if not location:
            return None
        
        if not isinstance(location, str):
            raise ValueError("Location must be a string")
        
        location = location.strip()
        
        if not cls.LOCATION_PATTERN.match(location):
            raise ValueError("Invalid location format")
        
        if cls._contains_malicious_content(location):
            raise ValueError("Location contains invalid characters")
        
        return location
    
    @classmethod
    def validate_description(cls, description: Optional[str]) -> Optional[str]:
        """Validate and sanitize description field"""
        if not description:
            return None
        
        if not isinstance(description, str):
            raise ValueError("Description must be a string")
        
        description = description.strip()
        
        if len(description) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        
        if cls._contains_malicious_content(description):
            raise ValueError("Description contain invalid characters")
        
        return description
    
    @classmethod
    def validate_meta_data(cls, meta_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate and sanitize meta_data"""
        if not meta_data:
            return None
        
        if not isinstance(meta_data, dict):
            raise ValueError("Metadata must be a dictionary")
        
        if len(meta_data) > 20:
            raise ValueError("Metadata cannot have more than 20 keys")
        
        sanitized = {}
        for key, value in meta_data.items():
            if not isinstance(key, str) or len(key) > 100:
                raise ValueError("Metadata keys must be strings with max 100 characters")
            
            if cls._contains_malicious_content(str(value)):
                raise ValueError(f"Metadata value for key '{key}' contains invalid characters")
            
            sanitized[key] = value
        
        return sanitized
    
    @classmethod
    def _contains_malicious_content(cls, content: str) -> bool:
        """Check if content contains malicious patterns"""
        for pattern in cls.BLOCKED_PATTERNS:
            if pattern.search(content):
                return True
        return False


class SecurityValidationError(HTTPException):
    """Custom exception for security validation errors"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security validation failed: {detail}"
        )