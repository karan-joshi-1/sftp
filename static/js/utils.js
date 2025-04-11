/**
 * Utility functions for the SFTP client
 */

/**
 * Format a file size in human-readable format
 * 
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size with units
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Get an appropriate icon for a file type based on its extension
 * 
 * @param {string} fileName - Name of the file
 * @returns {string} Font Awesome icon class
 */
function getFileIcon(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    
    const iconMap = {
        // Documents
        'txt': 'fa-file-alt',
        'pdf': 'fa-file-pdf',
        'doc': 'fa-file-word',
        'docx': 'fa-file-word',
        'xls': 'fa-file-excel',
        'xlsx': 'fa-file-excel',
        'ppt': 'fa-file-powerpoint',
        'pptx': 'fa-file-powerpoint',
        
        // Images
        'jpg': 'fa-file-image',
        'jpeg': 'fa-file-image',
        'png': 'fa-file-image',
        'gif': 'fa-file-image',
        'svg': 'fa-file-image',
        
        // Archives
        'zip': 'fa-file-archive',
        'rar': 'fa-file-archive',
        'tar': 'fa-file-archive',
        'gz': 'fa-file-archive',
        '7z': 'fa-file-archive',
        
        // Code
        'py': 'fa-file-code',
        'js': 'fa-file-code',
        'html': 'fa-file-code',
        'css': 'fa-file-code',
        'php': 'fa-file-code',
        'c': 'fa-file-code',
        'cpp': 'fa-file-code',
        'h': 'fa-file-code',
        'java': 'fa-file-code',
        'sh': 'fa-file-code',
        'json': 'fa-file-code',
        'xml': 'fa-file-code',
        
        // Media
        'mp3': 'fa-file-audio',
        'wav': 'fa-file-audio',
        'ogg': 'fa-file-audio',
        'mp4': 'fa-file-video',
        'avi': 'fa-file-video',
        'mov': 'fa-file-video',
        'mkv': 'fa-file-video'
    };
    
    return iconMap[extension] || 'fa-file';
}

/**
 * Handle API errors consistently
 * 
 * @param {Error} error - Error object
 * @returns {Object} Formatted error response
 */
function handleApiError(error) {
    console.error('API Error:', error);
    return {
        status: false,
        msg: error.message || 'An unexpected error occurred',
        data: {}
    };
}

/**
 * Show or hide a loading indicator on a button
 * 
 * @param {HTMLElement} button - Button element
 * @param {boolean} isLoading - Whether to show loading state
 */
function setButtonLoading(button, isLoading) {
    const loader = button.querySelector('.loader');
    const span = button.querySelector('span');
    
    if (isLoading) {
        loader.style.display = 'inline-block';
        button.classList.add('loading-button');
        span.style.visibility = 'hidden';
        button.disabled = true;
    } else {
        loader.style.display = 'none';
        button.classList.remove('loading-button');
        span.style.visibility = 'visible';
        button.disabled = false;
    }
}

/**
 * Show a loading state for the file list
 * 
 * @param {HTMLElement} fileList - File list element
 * @param {boolean} isLoading - Whether to show loading state
 */
function setFileListLoading(fileList, isLoading) {
    if (isLoading) {
        fileList.classList.add('loading');
        fileList.innerHTML = `
            <div class="file-item" style="justify-content: center; padding: 2rem;">
                <div class="loader"></div>
                <span style="margin-left: 0.75rem;">Loading files...</span>
            </div>
        `;
    } else {
        fileList.classList.remove('loading');
    }
}

/**
 * Add a status message to the status area
 * 
 * @param {HTMLElement} statusArea - Status area element
 * @param {string} message - Message to display
 * @param {string} type - Type of message ('success', 'error', or empty for info)
 */
function showStatus(statusArea, message, type = '') {
    const statusMsg = document.createElement('p');
    statusMsg.textContent = message;
    
    if (type === 'success') {
        statusMsg.className = 'success-message';
        statusMsg.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
    } else if (type === 'error') {
        statusMsg.className = 'error-message';
        statusMsg.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    }
    
    statusArea.appendChild(statusMsg);
    statusArea.scrollTop = statusArea.scrollHeight;
}