"""
Standardized response utilities
"""
from typing import Any, Dict, List, Optional, Union

def create_response(
    status: bool = False, 
    message: str = "", 
    data: Optional[Union[Dict, List, Any]] = None
) -> Dict:
    """
    Create a standardized API response
    
    Args:
        status: Boolean indicating success or failure
        message: Response message
        data: Response data
        
    Returns:
        Dict with status, message, and data
    """
    if data is None:
        data = {}
        
    return {
        "status": status,
        "msg": message,
        "data": data
    }

def success_response(
    data: Optional[Union[Dict, List, Any]] = None, 
    message: str = ""
) -> Dict:
    """
    Create a success response
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        Dict with success status, message, and data
    """
    return create_response(True, message, data)

def error_response(
    message: str, 
    data: Optional[Union[Dict, List, Any]] = None
) -> Dict:
    """
    Create an error response
    
    Args:
        message: Error message
        data: Additional error data
        
    Returns:
        Dict with error status, message, and data
    """
    return create_response(False, message, data)