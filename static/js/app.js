/**
 * Main application controller for the SFTP client
 */

/**
 * SFTP Client application
 */
class SftpClientApp {
    /**
     * Initialize the application
     * 
     * @param {ApiService} apiService - API service
     * @param {UiService} uiService - UI service
     */
    constructor(apiService, uiService) {
        this.api = apiService;
        this.ui = uiService;
        this.currentPath = '/';
        
        // Event handlers (bind to keep 'this' context)
        this.handlers = {
            connect: this.connect.bind(this),
            navigateUp: this.navigateUp.bind(this),
            navigateTo: this.navigateTo.bind(this),
            createNewFolder: this.createNewFolder.bind(this),
            refreshFileList: this.refreshFileList.bind(this),
            downloadFile: this.downloadFile.bind(this),
            deleteFile: this.deleteFile.bind(this),
            uploadFile: this.uploadFile.bind(this)
        };
        
        // Initialize UI event listeners
        this.ui.initEventListeners(this.handlers);
    }

    /**
     * Connect to SFTP server
     */
    async connect() {
        // Validate form
        if (!this.ui.validateLoginForm()) {
            this.ui.showStatus('Please fill in all connection fields', 'error');
            return;
        }
        
        const hostIp = this.ui.getInputValue('hostIp');
        const username = this.ui.getInputValue('username');
        const password = this.ui.getInputValue('password');
        
        try {
            // Show loading state
            this.ui.setButtonLoading('connectBtn', true);
            this.ui.showStatus(`Attempting to connect to ${hostIp} as ${username}...`);
            
            // Call API
            const response = await this.api.login(hostIp, username, password);
            
            // Hide loading state
            this.ui.setButtonLoading('connectBtn', false);
            
            if (response.status) {
                // Update UI for connected state
                this.ui.updateConnectionStatus(true, hostIp);
                this.ui.showStatus(`Connected successfully to ${hostIp} as ${username}`, 'success');
                this.ui.clearLoginForm();
                
                // Initialize file listing
                this.currentPath = '/';
                await this.refreshFileList();
                
                // Get disk usage (optional)
                this.api.getDiskUsage();
            } else {
                this.ui.showStatus(`Connection failed: ${response.msg}`, 'error');
            }
        } catch (error) {
            this.ui.setButtonLoading('connectBtn', false);
            this.ui.showStatus(`Error: ${error.message}`, 'error');
        }
    }

    /**
     * Refresh file listing
     */
    async refreshFileList() {
        if (!this.api.isConnected()) {
            this.ui.showStatus('Not connected to any server', 'error');
            return;
        }
        
        try {
            // Show loading state
            this.ui.setButtonLoading('refreshBtn', true);
            this.ui.setFileListLoading(true);
            this.ui.showStatus(`Loading files from ${this.currentPath}...`);
            
            // Call API
            const response = await this.api.listFiles(this.currentPath);
            
            // Always hide loading state, regardless of response
            this.ui.setButtonLoading('refreshBtn', false);
            this.ui.setFileListLoading(false);
            
            if (response.status) {
                // Update UI with files
                this.ui.displayFiles(response.data, this.handlers);
                this.ui.updatePathDisplay(this.currentPath);
                this.ui.updateDirectoryStats(response.data);
                this.ui.showStatus(`Loaded ${response.data.length} items from ${this.currentPath}`, 'success');
            } else {
                // Handle error response, but still clear loading state
                this.ui.showStatus(`Failed to list files: ${response.msg}`, 'error');
                
                // Show empty directory placeholder for permission errors or not found errors
                this.ui.elements.fileList.innerHTML = `
                    <div class="file-item">
                        <div class="file-info">
                            <i class="fas fa-exclamation-triangle file-icon"></i>
                            <span class="file-name">${response.msg || 'Error accessing directory'}</span>
                        </div>
                    </div>
                `;
                this.ui.updateDirectoryStats([]);
            }
        } catch (error) {
            // Ensure loading state is cleared even for unexpected errors
            this.ui.setButtonLoading('refreshBtn', false);
            this.ui.setFileListLoading(false);
            this.ui.showStatus(`Error: ${error.message}`, 'error');
            
            // Show error in file list
            this.ui.elements.fileList.innerHTML = `
                <div class="file-item">
                    <div class="file-info">
                        <i class="fas fa-exclamation-circle file-icon"></i>
                        <span class="file-name">An error occurred: ${error.message}</span>
                    </div>
                </div>
            `;
            this.ui.updateDirectoryStats([]);
        }
    }

    /**
     * Navigate to a specific path
     * 
     * @param {string} path - Path to navigate to
     */
    async navigateTo(path) {
        this.currentPath = path;
        await this.refreshFileList();
    }

    /**
     * Navigate up one directory
     */
    async navigateUp() {
        if (this.currentPath === '/') return;
        
        this.ui.setButtonLoading('upDirBtn', true);
        
        // Split path into parts and remove last part
        const parts = this.currentPath.split('/').filter(p => p);
        parts.pop();
        this.currentPath = '/' + parts.join('/');
        
        await this.refreshFileList();
        this.ui.setButtonLoading('upDirBtn', false);
    }

    /**
     * Create a new folder
     */
    async createNewFolder() {
        if (!this.api.isConnected()) {
            this.ui.showStatus('Not connected to any server', 'error');
            return;
        }
        
        const folderName = prompt('Enter folder name:');
        if (!folderName) return;
        
        const newPath = this.currentPath === '/' 
            ? `/${folderName}`
            : `${this.currentPath}/${folderName}`;
        
        try {
            // Show loading state
            this.ui.setButtonLoading('newFolderBtn', true);
            this.ui.showStatus(`Creating folder "${folderName}"...`);
            
            // Call API
            const response = await this.api.mkdir(newPath);
            
            // Hide loading state
            this.ui.setButtonLoading('newFolderBtn', false);
            
            if (response.status) {
                this.ui.showStatus(`Folder "${folderName}" created successfully`, 'success');
                await this.refreshFileList();
            } else {
                this.ui.showStatus(`Failed to create folder: ${response.msg}`, 'error');
            }
        } catch (error) {
            this.ui.setButtonLoading('newFolderBtn', false);
            this.ui.showStatus(`Error: ${error.message}`, 'error');
        }
    }

    /**
     * Download a file
     * 
     * @param {string} path - Path to file
     * @param {Event} event - Click event
     */
    async downloadFile(path, event) {
        if (!this.api.isConnected()) {
            this.ui.showStatus('Not connected to any server', 'error');
            return;
        }
        
        // Extract filename from path
        const filename = path.split('/').pop();
        
        // Get the button element from event if provided
        let downloadBtn = null;
        if (event && event.currentTarget) {
            downloadBtn = event.currentTarget;
            const originalHTML = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '<div class="loader"></div>';
            downloadBtn.disabled = true;
        }
        
        this.ui.showStatus(`Downloading ${filename}...`);
        
        try {
            // Call API
            const response = await this.api.getFile(path);
            
            // Restore button if provided
            if (downloadBtn) {
                downloadBtn.innerHTML = '<i class="fas fa-download"></i>';
                downloadBtn.disabled = false;
            }
            
            if (response instanceof Response) {
                // Handle successful file download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                
                // Create a temporary link to download the file
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                
                // Clean up
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.ui.showStatus(`Downloaded ${filename} successfully`, 'success');
            } else {
                // Handle error response
                this.ui.showStatus(`Download failed: ${response.msg}`, 'error');
            }
        } catch (error) {
            // Restore button if provided
            if (downloadBtn) {
                downloadBtn.innerHTML = '<i class="fas fa-download"></i>';
                downloadBtn.disabled = false;
            }
            
            this.ui.showStatus(`Error: ${error.message}`, 'error');
        }
    }

    /**
     * Delete a file or directory
     * 
     * @param {string} path - Path to delete
     * @param {Event} event - Click event
     */
    async deleteFile(path, event) {
        if (!this.api.isConnected()) {
            this.ui.showStatus('Not connected to any server', 'error');
            return;
        }
        
        if (!confirm(`Are you sure you want to delete "${path}"?`)) {
            return;
        }
        
        // Get the delete button from event if provided
        let deleteBtn = null;
        if (event && event.currentTarget) {
            deleteBtn = event.currentTarget;
            const originalHTML = deleteBtn.innerHTML;
            deleteBtn.innerHTML = '<div class="loader"></div>';
            deleteBtn.disabled = true;
        }
        
        try {
            this.ui.showStatus(`Deleting ${path}...`);
            
            // Call API
            const response = await this.api.remove(path);
            
            // Restore button if provided
            if (deleteBtn) {
                deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
                deleteBtn.disabled = false;
            }
            
            if (response.status) {
                this.ui.showStatus(`Deleted ${path} successfully`, 'success');
                await this.refreshFileList();
            } else {
                this.ui.showStatus(`Failed to delete: ${response.msg}`, 'error');
            }
        } catch (error) {
            // Restore button if provided
            if (deleteBtn) {
                deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
                deleteBtn.disabled = false;
            }
            
            this.ui.showStatus(`Error: ${error.message}`, 'error');
        }
    }

    /**
     * Upload a file
     */
    async uploadFile() {
        if (!this.api.isConnected()) {
            this.ui.showStatus('Not connected to any server', 'error');
            return;
        }
        
        const fileInput = this.ui.elements.fileUpload;
        if (!fileInput.files.length) {
            this.ui.showStatus('Please select a file to upload', 'error');
            return;
        }
        
        const file = fileInput.files[0];
        
        try {
            // Show loading state
            this.ui.setButtonLoading('uploadBtn', true);
            this.ui.showStatus(`Uploading ${file.name} to ${this.currentPath}...`);
            
            // Call API
            const response = await this.api.uploadFile(file, this.currentPath);
            
            // Hide loading state
            this.ui.setButtonLoading('uploadBtn', false);
            
            if (response.status) {
                this.ui.showStatus(`Uploaded ${file.name} successfully`, 'success');
                this.ui.resetForms();
                await this.refreshFileList();
            } else {
                this.ui.showStatus(`Upload failed: ${response.msg}`, 'error');
            }
        } catch (error) {
            this.ui.setButtonLoading('uploadBtn', false);
            this.ui.showStatus(`Error: ${error.message}`, 'error');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Create and start the application
    const app = new SftpClientApp(api, ui);
    
    // Log initialization
    console.log('SFTP Client initialized');
});