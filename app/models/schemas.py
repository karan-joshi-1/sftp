"""
Data models and schemas for request/response validation
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Client(BaseModel):
    """
    Authentication request model
    """
    hostIp: str = Field(..., description="Hostname or IP address, optionally with port (e.g. 192.168.1.1:22)")
    username: str = Field(..., description="SSH username")
    password: str = Field(..., description="SSH password")

class ConnectionInfo(BaseModel):
    """
    Connection information response model
    """
    key: str = Field(..., description="Connection key")
    hostIp: str = Field(..., description="Hostname or IP address")
    username: str = Field(..., description="Username")

class PathRequest(BaseModel):
    """
    Base model for path-related requests
    """
    hostIp: str = Field(..., description="Hostname or IP address")
    username: str = Field(..., description="Username")
    path: str = Field(..., description="File or directory path")

class ListFilesRequest(BaseModel):
    """
    Request model for listing files in a directory
    """
    hostIp: str = Field(..., description="Hostname or IP address")
    username: str = Field(..., description="Username")
    location: str = Field(..., description="Directory path to list")

class GetFileRequest(BaseModel):
    """
    Request model for downloading a file
    """
    hostIp: str = Field(..., description="Hostname or IP address")
    username: str = Field(..., description="Username")
    remotePath: str = Field(..., description="Path to the remote file")

class GetFileAfterRequest(BaseModel):
    """
    Request model for cleaning up after file download
    """
    fileName: str = Field(..., description="Name of the downloaded file")

class PathOperationRequest(BaseModel):
    """
    Request model for path operations like rename, copy
    """
    hostIp: str = Field(..., description="Hostname or IP address")
    username: str = Field(..., description="Username")
    oldPath: str = Field(..., description="Source path")
    newPath: str = Field(..., description="Destination path")

class FileInfo(BaseModel):
    """
    File or directory information model
    """
    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Full path")
    size: int = Field(..., description="Size in bytes")
    mTime: str = Field(..., description="Modified time")
    type: str = Field(..., description="File type: 'file' or 'dir'")

class UploadParams(BaseModel):
    """
    Upload parameters model for header parsing
    """
    hostIp: str = Field(..., description="Hostname or IP address")
    username: str = Field(..., description="Username")
    location: str = Field(..., description="Upload destination path")