"""
Client manager for SSH connections
"""
from typing import Dict, Optional, Tuple
from app.services.ssh_client import SSHClient
from app.utils.logger import get_logger

logger = get_logger()

class ClientManager:
    """
    Singleton class to manage SSH client connections
    """
    _instance = None
    _clients: Dict[str, SSHClient] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClientManager, cls).__new__(cls)
        return cls._instance
    
    def add_client(self, host_ip: str, username: str, password: str) -> Tuple[str, SSHClient]:
        """
        Create a new SSH client and add it to the manager
        
        Args:
            host_ip: Hostname/IP with optional port (format: hostname[:port])
            username: SSH username
            password: SSH password
            
        Returns:
            Tuple of (connection_key, client)
        """
        # Parse hostname and port
        if ':' in host_ip:
            hostname, port_str = host_ip.split(':', 1)
            port = int(port_str)
        else:
            hostname = host_ip
            port = 22
            
        # Create a unique key for this connection
        key = f"{host_ip}{username}"
        
        # Check if client already exists
        if key in self._clients:
            logger.info(f"Reusing existing connection for {key}")
            return key, self._clients[key]
        
        # Create a new client
        try:
            client = SSHClient(hostname, port, username, password)
            self._clients[key] = client
            logger.info(f"Added new client: {key}")
            return key, client
        except Exception as e:
            logger.error(f"Failed to create client: {str(e)}")
            raise
    
    def get_client(self, host_ip: str, username: str) -> Optional[SSHClient]:
        """
        Get an existing SSH client
        
        Args:
            host_ip: Hostname/IP with optional port
            username: SSH username
            
        Returns:
            SSHClient instance or None if not found
        """
        key = f"{host_ip}{username}"
        return self._clients.get(key)
    
    def get_client_by_key(self, key: str) -> Optional[SSHClient]:
        """
        Get an existing SSH client by its key
        
        Args:
            key: Connection key
            
        Returns:
            SSHClient instance or None if not found
        """
        return self._clients.get(key)
    
    def remove_client(self, key: str) -> bool:
        """
        Remove and close an SSH client
        
        Args:
            key: Connection key
            
        Returns:
            True if successful, False if client not found
        """
        if key in self._clients:
            try:
                # Close connection properly
                self._clients[key].close()
                # Remove from dictionary
                del self._clients[key]
                logger.info(f"Removed client: {key}")
                return True
            except Exception as e:
                logger.error(f"Error removing client {key}: {str(e)}")
                return False
        return False
    
    def get_all_clients(self) -> Dict[str, SSHClient]:
        """
        Get all active SSH clients
        
        Returns:
            Dictionary of all clients
        """
        return self._clients
    
    def cleanup(self):
        """
        Close all connections and clear the clients dictionary
        """
        for key, client in list(self._clients.items()):
            try:
                client.close()
                logger.info(f"Closed connection for {key}")
            except Exception as e:
                logger.error(f"Error closing connection for {key}: {str(e)}")
        
        self._clients.clear()
        logger.info("All client connections cleaned up")

# Create a singleton instance
client_manager = ClientManager()