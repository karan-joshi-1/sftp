"""
System information routes for the SFTP client
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import PathRequest
from app.services.client_manager import client_manager
from app.utils.response import success_response, error_response
from app.utils.logger import get_logger

logger = get_logger()
router = APIRouter(tags=["System Information"])

@router.post("/getHistory", summary="Get command history")
async def get_history(request: PathRequest):
    """
    Get command history from the remote server
    
    Args:
        request: PathRequest with connection information
        
    Returns:
        List of recent commands
    """
    try:
        # Get the client
        ssh_client = client_manager.get_client(request.hostIp, request.username)
        
        if not ssh_client:
            logger.warning(f"Client not found: {request.username}@{request.hostIp}")
            return error_response("Not logged in")
            
        # Get command history
        history = ssh_client.get_history()
        
        logger.info(f"Retrieved {len(history)} history entries for {request.username}@{request.hostIp}")
        return success_response(history)
        
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return error_response(str(e), [])

@router.post("/getDf", summary="Get disk usage")
async def get_df(request: PathRequest):
    """
    Get disk usage information from the remote server
    
    Args:
        request: PathRequest with connection information
        
    Returns:
        List of disk usage information lines
    """
    try:
        # Get the client
        ssh_client = client_manager.get_client(request.hostIp, request.username)
        
        if not ssh_client:
            logger.warning(f"Client not found: {request.username}@{request.hostIp}")
            return error_response("Not logged in")
            
        # Get disk usage
        df_info = ssh_client.get_df()
        
        logger.info(f"Retrieved disk usage information for {request.hostIp}")
        return success_response(df_info)
        
    except Exception as e:
        logger.error(f"Error getting disk usage: {str(e)}")
        return error_response(str(e), [])

@router.get("/status", summary="Get server status")
async def get_status():
    """
    Get SFTP server status and active connections
    
    Returns:
        Server status information
    """
    try:
        # Get all clients
        clients = client_manager.get_all_clients()
        
        # Create status information
        status = {
            "active_connections": len(clients),
            "connections": [
                {
                    "host": client.ip,
                    "username": client.username,
                    "connected_since": "Not implemented"  # Would require tracking connect time
                }
                for key, client in clients.items()
            ]
        }
        
        logger.info(f"Status request: {len(clients)} active connections")
        return success_response(status)
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return error_response(str(e), {})