/**
 * API service for communicating with the backend
 */

/**
 * SFTP Client API service
 */
class ApiService {
    /**
     * Initialize the API service
     */
    constructor() {
        this.baseUrl = ''; // Empty for same-origin requests
        this.connectionInfo = null;
    }

    /**
     * Make a generic API request
     * 
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} Response data
     */
    async request(endpoint, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30-second timeout
        
        try {
            const url = `${this.baseUrl}${endpoint}`;
            
            // Set default headers
            if (!options.headers) {
                options.headers = {
                    'Content-Type': 'application/json'
                };
            }
            
            // Add signal for timeout
            options.signal = controller.signal;
            
            const response = await fetch(url, options);
            
            // Clear timeout
            clearTimeout(timeoutId);
            
            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            // For non-JSON responses (like file downloads)
            return response;
            
        } catch (error) {
            // Clear timeout
            clearTimeout(timeoutId);
            
            // Handle specific error types
            if (error.name === 'AbortError') {
                return {
                    status: false,
                    msg: 'Request timed out. Please try again.',
                    data: {}
                };
            }
            
            return handleApiError(error);
        }
    }

    /**
     * Set connection information
     * 
     * @param {Object} connectionInfo - Connection information
     */
    setConnectionInfo(connectionInfo) {
        this.connectionInfo = connectionInfo;
    }

    /**
     * Get current connection information
     * 
     * @returns {Object|null} Connection information
     */
    getConnectionInfo() {
        return this.connectionInfo;
    }

    /**
     * Check if currently connected
     * 
     * @returns {boolean} Whether connected
     */
    isConnected() {
        return this.connectionInfo !== null;
    }

    /**
     * Clear connection information (logout)
     */
    clearConnectionInfo() {
        this.connectionInfo = null;
    }

    /**
     * Login to an SFTP server
     * 
     * @param {string} hostIp - Hostname or IP (with optional port)
     * @param {string} username - Username
     * @param {string} password - Password
     * @returns {Promise<Object>} Login response
     */
    async login(hostIp, username, password) {
        const response = await this.request('/login', {
            method: 'POST',
            body: JSON.stringify({ hostIp, username, password })
        });
        
        if (response.status) {
            this.setConnectionInfo(response.data);
        }
        
        return response;
    }

    /**
     * Logout from the SFTP server
     * 
     * @returns {Promise<Object>} Logout response
     */
    async logout() {
        if (!this.isConnected()) {
            return { status: false, msg: 'Not logged in', data: {} };
        }
        
        const response = await this.request('/logout', {
            method: 'POST',
            body: JSON.stringify(this.connectionInfo)
        });
        
        if (response.status) {
            this.clearConnectionInfo();
        }
        
        return response;
    }

    /**
     * List files in a directory
     * 
     * @param {string} location - Directory path
     * @returns {Promise<Object>} Directory listing
     */
    async listFiles(location) {
        if (!this.isConnected()) {
            return { status: false, msg: 'Not logged in', data: [{}] };
        }
        
        return await this.request('/listFiles', {
            method: 'POST',
            body: JSON.stringify({
                hostIp: this.connectionInfo.hostIp,
                username: this.connectionInfo.username,
                location: location
            })
        });
    }

    /**
     * Download a file
     * 
     * @param {string} remotePath - Path to remote file
     * @returns {Promise<Response>} File response
     */
    async getFile(remotePath) {
        if (!this.isConnected()) {
            return { status: false, msg: 'Not logged in', data: {} };
        }
        
        return await this.request('/getFile', {
            method: 'POST',
            body: JSON.stringify({
                hostIp: this.connectionInfo.hostIp,
                username: this.connectionInfo.username,
                remotePath: remotePath
            })
        });
    }

    /**
     * Upload a file
     * 
     * @param {File} file - File to upload
     * @param {string} location - Destination directory
     * @returns {Promise<Object>} Upload response
     */
    async uploadFile(file, location) {
        if (!this.isConnected()) {
            return { status: false, msg: 'Not logged in', data: {} };
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        const uploadParams = {
            hostIp: this.connectionInfo.hostIp,
            username: this.connectionInfo.username,
            location: location
        };
        
        return await this.request('/uploadfile', {
            method: 'POST',
            headers: {
                'upload-params': JSON.stringify(uploadParams),
                'file-size': file.size.toString()
            },
            body: formData
        });
    }

    /**
     * Create a new directory
     * 
     * @param {string} path - Path for new directory
     * @returns {Promise<Object>} Create directory response
     */
    async mkdir(path) {
        if (!this.isConnected()) {
            return { status: false, msg: 'Not logged in', data: {} };
        }
        
        return await this.request('/mkdir', {
            method: 'POST',
            body: JSON.stringify({
                hostIp: this.connectionInfo.hostIp,
                username: this.connectionInfo.username,
                path: path
            })
        });
    }

    /**
     * Delete a file or directory
     * 
     * @param {string} path - Path to delete
     * @returns {Promise<Object>} Delete response
     */
    async remove(path) {
        if (!this.isConnected()) {
            return { status: false, msg: 'Not logged in', data: {} };
        }
        
        return await this.request('/remove', {
            method: 'POST',
            body: JSON.stringify({
                hostIp: this.connectionInfo.hostIp,
                username: this.connectionInfo.username,
                path: path
            })
        });
    }

    /**
     * Rename a file or directory
     * 
     * @param {string} oldPath - Original path
     * @param {string} newPath - New path
     * @returns {Promise<Object>} Rename response
     */
    async rename(oldPath, newPath) {
        if (!this.isConnected()) {
            return { status: false, msg: 'Not logged in', data: {} };
        }
        
        return await this.request('/rename', {
            method: 'POST',
            body: JSON.stringify({
                hostIp: this.connectionInfo.hostIp,
                username: this.connectionInfo.username,
                oldPath: oldPath,
                newPath: newPath
            })
        });
    }

    /**
     * Get disk usage information
     * 
     * @returns {Promise<Object>} Disk usage information
     */
    async getDiskUsage() {
        if (!this.isConnected()) {
            return { status: false, msg: 'Not logged in', data: [] };
        }
        
        return await this.request('/getDf', {
            method: 'POST',
            body: JSON.stringify({
                hostIp: this.connectionInfo.hostIp,
                username: this.connectionInfo.username,
                path: '/'
            })
        });
    }

    /**
     * Get command history
     * 
     * @returns {Promise<Object>} Command history
     */
    async getHistory() {
        if (!this.isConnected()) {
            return { status: false, msg: 'Not logged in', data: [] };
        }
        
        return await this.request('/getHistory', {
            method: 'POST',
            body: JSON.stringify({
                hostIp: this.connectionInfo.hostIp,
                username: this.connectionInfo.username,
                path: '/'
            })
        });
    }

    /**
     * Get server status information
     * 
     * @returns {Promise<Object>} Server status
     */
    async getStatus() {
        return await this.request('/status', {
            method: 'GET'
        });
    }
}

// Create a singleton instance
const api = new ApiService();