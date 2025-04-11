"""
File operation routes for the SFTP client
"""
import os
import json
import mimetypes
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import ValidationError

from app.models.schemas import (
    ListFilesRequest, 
    GetFileRequest, 
    PathRequest, 
    PathOperationRequest,
    UploadParams
)
from app.services.client_manager import client_manager
from app.utils.response import success_response, error_response
from app.utils.logger import get_logger
from app.config import get_settings

logger = get_logger()
router = APIRouter(tags=["File Operations"])
settings = get_settings()

def cleanup_temp_file(file_path: str):
    """
    Background task to clean up temporary files
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {str(e)}")

@router.post("/listFiles", summary="List files in a directory")
async def list_files(request: ListFilesRequest):
    """
    List files and directories in a specified path
    
    Args:
        request: ListFilesRequest with connection and path information
        
    Returns:
        List of file and directory information
    """
    try:
        # Get the client
        ssh_client = client_manager.get_client(request.hostIp, request.username)
        
        if not ssh_client:
            logger.warning(f"Client not found: {request.username}@{request.hostIp}")
            return error_response("Not logged in")
            
        # Get file listing
        try:
            all_files = ssh_client.get_all_files_in_remote_dir(request.location)
            
            logger.info(f"Listed {len(all_files)} files in {request.location}")
            return success_response(all_files)
            
        except PermissionError:
            logger.error(f"Permission denied accessing {request.location}")
            return error_response(f"Permission denied for {request.location}", [])
            
        except FileNotFoundError:
            logger.error(f"Directory not found: {request.location}")
            return error_response(f"Directory not found: {request.location}", [])
        
    except Exception as e:
        logger.error(f"Error listing files in {request.location}: {str(e)}")
        return error_response(str(e), [])

@router.post("/getFile", summary="Download a file")
async def get_file(request: GetFileRequest, background_tasks: BackgroundTasks):
    """
    Download a file from the remote server
    
    Args:
        request: GetFileRequest with file path information
        background_tasks: FastAPI background tasks
        
    Returns:
        File content as a streaming response
    """
    try:
        # Get the client
        ssh_client = client_manager.get_client(request.hostIp, request.username)
        
        if not ssh_client:
            logger.warning(f"Client not found: {request.username}@{request.hostIp}")
            return error_response("Not logged in")
            
        # Get file name from path
        pos = request.remotePath.rfind('/')
        file_name = request.remotePath[pos:]
        
        # Download the file
        success = ssh_client.get_file(request.remotePath, settings.tmp_path)
        
        if not success:
            logger.error(f"Failed to download {request.remotePath}")
            return error_response("Failed to download file")
        
        # Prepare file path
        path = settings.tmp_path + file_name
        path = path.replace('//', '/')
        
        # Determine content type
        content_type = mimetypes.guess_type(path)[0]
        if not content_type:
            content_type = "application/octet-stream"
            
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_file, path)
        
        logger.info(f"Downloaded {request.remotePath} to {path}")
        
        # Return file as response
        return FileResponse(
            path=path,
            media_type=content_type,
            filename=os.path.basename(path)
        )
        
    except Exception as e:
        logger.error(f"Error downloading {request.remotePath}: {str(e)}")
        return error_response(str(e))

@router.post("/uploadfile", summary="Upload a file")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """
    Upload a file to the remote server
    
    Args:
        request: FastAPI request with upload parameters in headers
        file: File to upload
        
    Returns:
        Success or error message with filename
    """
    try:
        # Parse upload parameters from headers
        try:
            upload_params_json = request.headers.get('upload-params', '{}')
            upload_params = json.loads(upload_params_json)
            
            # Validate parameters
            params = UploadParams(**upload_params)
            host_ip = params.hostIp
            username = params.username
            location = params.location
            
        except (ValidationError, json.JSONDecodeError) as e:
            logger.error(f"Invalid upload parameters: {str(e)}")
            return error_response("Invalid upload parameters")
        
        # Get file size from headers
        try:
            file_size = int(request.headers.get('file-size', '0'))
        except ValueError:
            file_size = 0
            
        # Get the client
        ssh_client = client_manager.get_client(host_ip, username)
        
        if not ssh_client:
            logger.warning(f"Client not found: {username}@{host_ip}")
            return error_response("Not logged in")
            
        # Save file to temporary location
        local_path = os.path.join(settings.upload_tmp_path, file.filename)
        
        with open(local_path, 'wb') as f:
            contents = await file.read()
            f.write(contents)
            
        # Upload to remote server
        remote_path = f"{location}/{file.filename}"
        success = ssh_client.put(local_path, remote_path)
        
        # Clean up temporary file
        cleanup_temp_file(local_path)
        
        if success:
            logger.info(f"Uploaded {file.filename} to {remote_path}")
            return success_response({"filename": file.filename}, "File uploaded successfully")
        else:
            logger.error(f"Failed to upload {file.filename} to {remote_path}")
            return error_response("Failed to upload file")
            
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return error_response(str(e))

@router.post("/mkdir", summary="Create a directory")
async def mkdir(request: PathRequest):
    """
    Create a new directory on the remote server
    
    Args:
        request: PathRequest with directory path
        
    Returns:
        Success or error message
    """
    try:
        # Get the client
        ssh_client = client_manager.get_client(request.hostIp, request.username)
        
        if not ssh_client:
            logger.warning(f"Client not found: {request.username}@{request.hostIp}")
            return error_response("Not logged in")
            
        # Create directory
        success = ssh_client.mkdir(request.path)
        
        if success:
            logger.info(f"Created directory {request.path}")
            return success_response(message="Directory created successfully")
        else:
            logger.error(f"Failed to create directory {request.path}")
            return error_response("Failed to create directory")
            
    except Exception as e:
        logger.error(f"Error creating directory {request.path}: {str(e)}")
        return error_response(str(e))

@router.post("/remove", summary="Delete a file or directory")
async def remove(request: PathRequest):
    """
    Delete a file or directory on the remote server
    
    Args:
        request: PathRequest with path to delete
        
    Returns:
        Success or error message
    """
    try:
        # Get the client
        ssh_client = client_manager.get_client(request.hostIp, request.username)
        
        if not ssh_client:
            logger.warning(f"Client not found: {request.username}@{request.hostIp}")
            return error_response("Not logged in")
            
        # Remove file or directory
        success = ssh_client.remove(request.path)
        
        if success:
            logger.info(f"Removed {request.path}")
            return success_response(message="File/directory removed successfully")
        else:
            logger.error(f"Failed to remove {request.path}")
            return error_response("Failed to remove or path protected")
            
    except Exception as e:
        logger.error(f"Error removing {request.path}: {str(e)}")
        return error_response(str(e))

@router.post("/rename", summary="Rename a file or directory")
async def rename(request: PathOperationRequest):
    """
    Rename a file or directory on the remote server
    
    Args:
        request: PathOperationRequest with old and new paths
        
    Returns:
        Success or error message
    """
    try:
        # Get the client
        ssh_client = client_manager.get_client(request.hostIp, request.username)
        
        if not ssh_client:
            logger.warning(f"Client not found: {request.username}@{request.hostIp}")
            return error_response("Not logged in")
            
        # Rename file or directory
        success = ssh_client.rename(request.oldPath, request.newPath)
        
        if success:
            logger.info(f"Renamed {request.oldPath} to {request.newPath}")
            return success_response(message="File/directory renamed successfully")
        else:
            logger.error(f"Failed to rename {request.oldPath} to {request.newPath}")
            return error_response("Failed to rename")
            
    except Exception as e:
        logger.error(f"Error renaming {request.oldPath} to {request.newPath}: {str(e)}")
        return error_response(str(e))