"""
SSH client implementation for SFTP operations
"""
import os
import stat
import time
import paramiko
from typing import List, Dict, Any, Tuple, Optional
from app.utils.logger import get_logger

logger = get_logger()

class EnhancedTransport(paramiko.Transport):
    """
    Enhanced SSH transport with optimized parameters
    """
    def __init__(self, sock):
        super(EnhancedTransport, self).__init__(sock)
        # Increased window size for better performance
        self.window_size = 3 * 1024 * 1024
        # Extended rekeying parameters to reduce overhead
        self.packetizer.REKEY_BYTES = pow(2, 40)
        self.packetizer.REKEY_PACKETS = pow(2, 40)


class SSHClient:
    """
    SSH client for file operations and command execution
    """
    def __init__(self, ip: str, port: int = 22, username: str = None, password: str = None):
        """
        Initialize SSH client with connection parameters
        
        Args:
            ip: IP address or hostname
            port: SSH port (default: 22)
            username: SSH username
            password: SSH password
        """
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        
        # Connection key for client management
        self.key = f"{ip}:{port}:{username}"
        
        # Protected system directories
        self.protected_dirs = [
            '/bin', '/boot', '/dev', '/etc',
            '/home', '/lib', '/opt', '/proc',
            '/root', '/sbin', '/tmp', '/usr',
            '/var'
        ]
        
        # Initialize transport with enhanced parameters
        self.transport = EnhancedTransport((self.ip, self.port))
        self.transport.connect(username=self.username, password=self.password)
        self.transport.use_compression()
        
        # Initialize SFTP client
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        
        # Initialize SSH client for command execution
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.ip, self.port, self.username, self.password)
        
        logger.info(f"SSH connection established to {ip}:{port} as {username}")
    
    def __del__(self):
        """
        Clean up connections when object is destroyed
        """
        self.close()
    
    def close(self):
        """
        Close SSH and SFTP connections
        """
        try:
            if hasattr(self, 'transport') and self.transport:
                self.transport.close()
            
            if hasattr(self, 'ssh') and self.ssh:
                self.ssh.close()
                
            logger.info(f"SSH connection closed for {self.ip}:{self.port}")
        except Exception as e:
            logger.error(f"Error closing SSH connection: {str(e)}")
    
    def get_all_files_in_remote_dir(self, remote_dir: str) -> List[Dict[str, Any]]:
        """
        Get all files and directories in a remote directory
        
        Args:
            remote_dir: Path to remote directory
            
        Returns:
            List of dictionaries with file/directory information
        
        Raises:
            PermissionError: If access to the directory is denied
            FileNotFoundError: If the directory doesn't exist
            Exception: For other errors
        """
        all_files = []
        
        # Normalize path
        if remote_dir[-1] == '/':
            remote_dir = remote_dir[0:-1]
    
        if remote_dir == '':
            remote_dir = '/'
        
        logger.debug(f"Listing files in {remote_dir}")
        
        try:
            # First check if we can access the directory
            try:
                # Use stat to check if directory exists and is accessible
                self.sftp.stat(remote_dir)
            except IOError as e:
                if 'Permission denied' in str(e):
                    logger.error(f"Permission denied accessing directory: {remote_dir}")
                    raise PermissionError(f"Permission denied for {remote_dir}")
                elif 'No such file' in str(e):
                    logger.error(f"Directory not found: {remote_dir}")
                    raise FileNotFoundError(f"Directory not found: {remote_dir}")
                else:
                    raise
            
            # Get directory listing with attributes
            files = self.sftp.listdir_attr(remote_dir)
            
            for file_attr in files:
                # Construct full path
                if remote_dir == '/':
                    file_path = f"/{file_attr.filename}"
                else:
                    file_path = f"{remote_dir}/{file_attr.filename}"
                
                # Determine if it's a directory or file
                is_dir = stat.S_ISDIR(file_attr.st_mode)
                
                # Create file info dictionary
                file_info = {
                    'name': file_attr.filename,
                    'path': file_path,
                    'size': file_attr.st_size,
                    'mTime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_attr.st_mtime)),
                    'type': 'dir' if is_dir else 'file'
                }
                
                all_files.append(file_info)
            
            return all_files
        
        except PermissionError as e:
            logger.error(f"Permission denied accessing directory: {remote_dir}")
            raise
        except FileNotFoundError as e:
            logger.error(f"Directory not found: {remote_dir}")
            raise
        except Exception as e:
            logger.error(f"Error listing files in {remote_dir}: {str(e)}")
            raise
    
    def put(self, local_path: str, remote_path: str) -> bool:
        """
        Upload a file to the remote server
        
        Args:
            local_path: Path to local file
            remote_path: Destination path on remote server
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Uploading {local_path} to {remote_path}")
            self.sftp.put(localpath=local_path, remotepath=remote_path)
            return True
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return False
    
    def get_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download a file from the remote server
        
        Args:
            remote_path: Path to file on remote server
            local_path: Local directory where file will be saved
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract filename from remote path
            pos = remote_path.rfind('/')
            local_filename = remote_path[pos:]
            
            # Format local path
            if local_path.endswith('/'):
                local_path = local_path[:-1]
            
            # Create full path
            save_path = local_path + local_filename
            
            logger.info(f"Downloading {remote_path} to {save_path}")
            
            # Download file
            self.sftp.get(remote_path, save_path)
            return True
            
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return False
    
    def remove(self, file_path: str) -> bool:
        """
        Delete a file or directory on the remote server
        
        Args:
            file_path: Path to the file or directory to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Safety checks
        if file_path == '/':
            logger.warning("Attempted to delete root directory")
            return False
        
        # Check if this is a protected directory
        for protected_dir in self.protected_dirs:
            if file_path == protected_dir or file_path.startswith(f"{protected_dir}/"):
                logger.warning(f"Attempted to delete protected directory: {file_path}")
                return False
        
        try:
            logger.info(f"Removing {file_path}")
            
            # Use rm command for flexibility with directories and files
            stdin, stdout, stderr = self.ssh.exec_command(f'rm -rf "{file_path}"')
            
            # Wait for command to complete and check exit status
            exit_status = stdout.channel.recv_exit_status()
            error = stderr.read().decode().strip()
            
            if exit_status != 0 or error:
                logger.error(f"Error removing {file_path}: {error}, exit status: {exit_status}")
                return False
            
            # Verify file was deleted
            try:
                # Try to stat the file - if this succeeds, it wasn't deleted
                stdin, stdout, stderr = self.ssh.exec_command(f'stat "{file_path}" 2>/dev/null')
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status == 0:
                    logger.error(f"File still exists after deletion attempt: {file_path}")
                    return False
            except Exception:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing {file_path}: {str(e)}")
            return False
    
    def rename(self, old_path: str, new_path: str) -> bool:
        """
        Rename a file or directory on the remote server
        
        Args:
            old_path: Original path
            new_path: New path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Renaming {old_path} to {new_path}")
            self.sftp.rename(old_path, new_path)
            return True
        except Exception as e:
            logger.error(f"Error renaming {old_path} to {new_path}: {str(e)}")
            return False
    
    def mkdir(self, dir_path: str) -> bool:
        """
        Create a new directory on the remote server
        
        Args:
            dir_path: Path for the new directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Creating directory {dir_path}")
            self.sftp.mkdir(dir_path)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {dir_path}: {str(e)}")
            return False
    
    def get_history(self) -> List[str]:
        """
        Get command history from the remote server
        
        Returns:
            List of recent commands
        """
        try:
            logger.info(f"Getting command history for {self.username}")
            stdin, stdout, stderr = self.ssh.exec_command("cat ~/.bash_history")
            
            history = []
            for line in stdout.readlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    history.append(line)
            
            return history
        except Exception as e:
            logger.error(f"Error getting command history: {str(e)}")
            return []
    
    def get_df(self) -> List[str]:
        """
        Get disk usage information from the remote server
        
        Returns:
            List of disk usage information lines
        """
        try:
            logger.info(f"Getting disk usage for {self.ip}")
            stdin, stdout, stderr = self.ssh.exec_command("df -h")
            
            df_output = []
            for line in stdout.readlines():
                df_output.append(line.strip())
            
            return df_output
        except Exception as e:
            logger.error(f"Error getting disk usage: {str(e)}")
            return []