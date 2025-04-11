"""
Authentication routes for the SFTP client
"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import Client, ConnectionInfo
from app.services.client_manager import client_manager
from app.utils.response import success_response, error_response
from app.utils.logger import get_logger

logger = get_logger()
router = APIRouter(tags=["Authentication"])

@router.post("/login", summary="Login to SSH server")
async def login(client: Client):
    """
    Connect to an SSH server with provided credentials
    
    Args:
        client: Authentication request with hostIp, username, and password
        
    Returns:
        Connection information including connection key
    """
    try:
        # Attempt to create SSH client
        key, ssh_client = client_manager.add_client(
            client.hostIp, 
            client.username, 
            client.password
        )
        
        # Create response data
        connection_info = {
            "key": key,
            "hostIp": client.hostIp,
            "username": client.username
        }
        
        logger.info(f"Successful login: {client.username}@{client.hostIp}")
        return success_response(connection_info, "Login successful")
        
    except Exception as e:
        logger.error(f"Login failed for {client.username}@{client.hostIp}: {str(e)}")
        return error_response(f"Login failed: {str(e)}")

@router.post("/logout", summary="Logout from SSH server")
async def logout(client: ConnectionInfo):
    """
    Disconnect from an SSH server
    
    Args:
        client: Connection information including key
        
    Returns:
        Success or error message
    """
    try:
        # Remove the client
        if client_manager.remove_client(client.key):
            logger.info(f"Successful logout: {client.username}@{client.hostIp}")
            return success_response(message="Logout successful")
        else:
            logger.warning(f"Logout failed - client not found: {client.username}@{client.hostIp}")
            return error_response("Client not found")
            
    except Exception as e:
        logger.error(f"Logout error for {client.username}@{client.hostIp}: {str(e)}")
        return error_response(f"Logout failed: {str(e)}")