/**
 * UI component handling for the SFTP client
 */

/**
 * SFTP Client UI service
 */
class UiService {
    /**
     * Initialize the UI service
     */
    constructor() {
        // DOM elements
        this.elements = {
            connectBtn: document.getElementById('connectBtn'),
            upDirBtn: document.getElementById('upDirBtn'),
            newFolderBtn: document.getElementById('newFolderBtn'),
            refreshBtn: document.getElementById('refreshBtn'),
            uploadBtn: document.getElementById('uploadBtn'),
            fileList: document.getElementById('fileList'),
            currentPath: document.getElementById('currentPath'),
            uploadForm: document.getElementById('uploadForm'),
            fileUpload: document.getElementById('fileUpload'),
            connectionStatus: document.getElementById('connectionStatus'),
            statusArea: document.getElementById('statusArea'),
            dirStats: document.getElementById('dirStats'),
            hostIp: document.getElementById('hostIp'),
            username: document.getElementById('username'),
            password: document.getElementById('password')
        };
    }

    /**
     * Initialize event listeners
     * 
     * @param {Object} handlers - Event handler functions
     */
    initEventListeners(handlers) {
        // Connection form
        this.elements.connectBtn.addEventListener('click', handlers.connect);
        
        // Navigation
        this.elements.upDirBtn.addEventListener('click', handlers.navigateUp);
        this.elements.newFolderBtn.addEventListener('click', handlers.createNewFolder);
        this.elements.refreshBtn.addEventListener('click', handlers.refreshFileList);
        
        // Upload
        this.elements.uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handlers.uploadFile();
        });
    }

    /**
     * Update connection status display
     * 
     * @param {boolean} isConnected - Connection status
     * @param {string} hostIp - Connected host (if connected)
     */
    updateConnectionStatus(isConnected, hostIp = '') {
        const status = this.elements.connectionStatus;
        
        if (isConnected) {
            status.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <span>Connected to ${hostIp}</span>
            `;
            status.className = 'connection-status connected';
        } else {
            status.innerHTML = `
                <i class="fas fa-times-circle"></i>
                <span>Not connected</span>
            `;
            status.className = 'connection-status';
        }
    }

    /**
     * Update current path display
     * 
     * @param {string} path - Current path
     */
    updatePathDisplay(path) {
        this.elements.currentPath.textContent = path;
    }

    /**
     * Update directory statistics
     * 
     * @param {Array} files - Array of file/directory objects
     */
    updateDirectoryStats(files) {
        const dirs = files.filter(f => f.type === 'dir').length;
        const filesCount = files.filter(f => f.type === 'file').length;
        
        this.elements.dirStats.textContent = `${dirs} ${dirs === 1 ? 'directory' : 'directories'}, ${filesCount} ${filesCount === 1 ? 'file' : 'files'}`;
    }

    /**
     * Display files in the file list
     * 
     * @param {Array} files - Array of file/directory objects
     * @param {Object} handlers - Event handler functions
     */
    displayFiles(files, handlers) {
        this.elements.fileList.innerHTML = '';
        
        if (files.length === 0) {
            this.elements.fileList.innerHTML = `
                <div class="file-item">
                    <div class="file-info">
                        <i class="fas fa-info-circle file-icon"></i>
                        <span class="file-name">Empty directory</span>
                    </div>
                </div>
            `;
            return;
        }
        
        // Sort: directories first, then files alphabetically
        files.sort((a, b) => {
            if (a.type === 'dir' && b.type !== 'dir') return -1;
            if (a.type !== 'dir' && b.type === 'dir') return 1;
            return a.name.localeCompare(b.name);
        });
        
        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = `file-item ${file.type}`;
            
            // Determine icon and format size
            let fileIcon, fileSize;
            if (file.type === 'dir') {
                fileIcon = 'fa-folder';
            } else {
                fileIcon = getFileIcon(file.name);
                fileSize = formatFileSize(file.size);
            }
            
            // Create file item HTML
            const fileHtml = `
                <div class="file-info">
                    <i class="fas ${fileIcon} file-icon"></i>
                    <div class="file-details">
                        <span class="file-name">${file.name}</span>
                        ${file.type === 'file' ? `<span class="file-meta">${fileSize} • ${file.mTime}</span>` : ''}
                    </div>
                </div>
                <div class="item-actions">
                    ${file.type === 'file' ? `
                        <button class="btn btn-secondary download-btn">
                            <i class="fas fa-download"></i>
                        </button>
                    ` : ''}
                    <button class="btn btn-danger delete-btn">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            `;
            
            fileItem.innerHTML = fileHtml;
            
            // Add event listeners
            if (file.type === 'dir') {
                fileItem.querySelector('.file-info').addEventListener('click', () => {
                    handlers.navigateTo(file.path);
                });
            }
            
            if (file.type === 'file') {
                fileItem.querySelector('.download-btn').addEventListener('click', (e) => {
                    e.stopPropagation();
                    handlers.downloadFile(file.path);
                });
            }
            
            fileItem.querySelector('.delete-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                handlers.deleteFile(file.path);
            });
            
            this.elements.fileList.appendChild(fileItem);
        });
    }

    /**
     * Show or hide loading indicator on a button
     * 
     * @param {string} buttonId - Button ID
     * @param {boolean} isLoading - Whether to show loading state
     */
    setButtonLoading(buttonId, isLoading) {
        const button = this.elements[buttonId];
        if (button) {
            setButtonLoading(button, isLoading);
        }
    }

    /**
     * Show loading state for file list
     * 
     * @param {boolean} isLoading - Whether to show loading state
     */
    setFileListLoading(isLoading) {
        if (isLoading) {
            this.elements.fileList.classList.add('loading');
            this.elements.fileList.innerHTML = `
                <div class="file-item" style="justify-content: center; padding: 2rem;">
                    <div class="loader"></div>
                    <span style="margin-left: 0.75rem;">Loading files...</span>
                </div>
            `;
            
            // Safety timeout - never stay in loading state for more than 30 seconds
            if (this._loadingTimeout) {
                clearTimeout(this._loadingTimeout);
            }
            
            this._loadingTimeout = setTimeout(() => {
                if (this.elements.fileList.classList.contains('loading')) {
                    this.setFileListLoading(false);
                    this.elements.fileList.innerHTML = `
                        <div class="file-item">
                            <div class="file-info">
                                <i class="fas fa-exclamation-triangle file-icon"></i>
                                <span class="file-name">Loading timed out. Please try again.</span>
                            </div>
                        </div>
                    `;
                    this.showStatus('Loading timed out. Please try again.', 'error');
                }
            }, 30000); // 30 second timeout
        } else {
            // Clear the safety timeout if loading finishes normally
            if (this._loadingTimeout) {
                clearTimeout(this._loadingTimeout);
                this._loadingTimeout = null;
            }
            
            this.elements.fileList.classList.remove('loading');
        }
    }

    /**
     * Add a status message
     * 
     * @param {string} message - Message to display
     * @param {string} type - Message type ('success', 'error', or empty)
     */
    showStatus(message, type = '') {
        showStatus(this.elements.statusArea, message, type);
    }

    /**
     * Reset form inputs
     */
    resetForms() {
        this.elements.fileUpload.value = '';
    }

    /**
     * Get the value of a form input
     * 
     * @param {string} inputId - Input element ID
     * @returns {string} Input value
     */
    getInputValue(inputId) {
        return this.elements[inputId] ? this.elements[inputId].value : '';
    }

    /**
     * Clear the form inputs after login
     */
    clearLoginForm() {
        // Only clear password for security
        this.elements.password.value = '';
    }

    /**
     * Check if login form is valid
     * 
     * @returns {boolean} Whether form is valid
     */
    validateLoginForm() {
        const hostIp = this.getInputValue('hostIp');
        const username = this.getInputValue('username');
        const password = this.getInputValue('password');
        
        return hostIp && username && password;
    }
}

// Create a singleton instance
const ui = new UiService();