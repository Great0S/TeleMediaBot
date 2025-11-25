// ==================== Utility Functions ====================

// String utilities
const StringUtils = {
    // Escape HTML to prevent XSS
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    },

    // Truncate text with ellipsis
    truncate(text, maxLength = 100) {
        if (text.length <= maxLength) return text;
        return text.slice(0, maxLength) + '...';
    },

    // Convert string to slug
    slugify(text) {
        return text
            .toLowerCase()
            .trim()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }
};

// Date/Time utilities
const DateUtils = {
    // Format date to readable string
    formatDate(date, format = 'default') {
        const d = new Date(date);

        if (format === 'relative') {
            return this.getRelativeTime(d);
        }

        const options = {
            default: { year: 'numeric', month: 'short', day: 'numeric' },
            long: { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' },
            short: { month: 'short', day: 'numeric' },
            time: { hour: '2-digit', minute: '2-digit' }
        };

        return d.toLocaleDateString('en-US', options[format] || options.default);
    },

    // Get relative time (e.g., "2 hours ago")
    getRelativeTime(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (seconds < 60) return 'just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        if (days < 30) return `${Math.floor(days / 7)}w ago`;
        if (days < 365) return `${Math.floor(days / 30)}mo ago`;
        return `${Math.floor(days / 365)}y ago`;
    },

    // Format timestamp
    formatTimestamp(timestamp) {
        return this.formatDate(timestamp * 1000, 'long');
    }
};

// Number/File utilities
const NumberUtils = {
    // Format bytes to human readable size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    },

    // Format number with commas
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    // Format percentage
    formatPercent(value, total, decimals = 1) {
        if (total === 0) return '0%';
        return ((value / total) * 100).toFixed(decimals) + '%';
    }
};

// Array utilities
const ArrayUtils = {
    // Group array items by key
    groupBy(array, key) {
        return array.reduce((result, item) => {
            const group = item[key];
            if (!result[group]) {
                result[group] = [];
            }
            result[group].push(item);
            return result;
        }, {});
    },

    // Remove duplicates from array
    unique(array) {
        return [...new Set(array)];
    },

    // Chunk array into smaller arrays
    chunk(array, size) {
        const chunks = [];
        for (let i = 0; i < array.length; i += size) {
            chunks.push(array.slice(i, i + size));
        }
        return chunks;
    }
};

// URL/Query utilities
const UrlUtils = {
    // Build query string from object
    buildQueryString(params) {
        return Object.keys(params)
            .filter(key => params[key] !== null && params[key] !== undefined)
            .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
            .join('&');
    },

    // Parse query string to object
    parseQueryString(queryString) {
        const params = {};
        const urlParams = new URLSearchParams(queryString);
        for (const [key, value] of urlParams) {
            params[key] = value;
        }
        return params;
    },

    // Update URL without reload
    updateUrl(params, replace = false) {
        const url = new URL(window.location);
        Object.keys(params).forEach(key => {
            if (params[key] === null || params[key] === undefined) {
                url.searchParams.delete(key);
            } else {
                url.searchParams.set(key, params[key]);
            }
        });

        if (replace) {
            window.history.replaceState({}, '', url);
        } else {
            window.history.pushState({}, '', url);
        }
    }
};

// API utilities
const ApiUtils = {
    // Fetch with error handling
    async fetch(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            if (window.Toast) {
                window.Toast.error(error.message || 'Request failed');
            }
            throw error;
        }
    },

    // GET request
    async get(url, params = {}) {
        const queryString = UrlUtils.buildQueryString(params);
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        return this.fetch(fullUrl, { method: 'GET' });
    },

    // POST request
    async post(url, data = {}) {
        return this.fetch(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // PUT request
    async put(url, data = {}) {
        return this.fetch(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    // DELETE request
    async delete(url) {
        return this.fetch(url, { method: 'DELETE' });
    }
};

// DOM utilities
const DomUtils = {
    // Create element with attributes
    createElement(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);

        Object.keys(attributes).forEach(key => {
            if (key === 'class') {
                element.className = attributes[key];
            } else if (key === 'style' && typeof attributes[key] === 'object') {
                Object.assign(element.style, attributes[key]);
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, attributes[key]);
            } else {
                element[key] = attributes[key];
            }
        });

        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else {
                element.appendChild(child);
            }
        });

        return element;
    },

    // Show/hide element
    show(selector) {
        const element = typeof selector === 'string' ? document.querySelector(selector) : selector;
        if (element) element.style.display = '';
    },

    hide(selector) {
        const element = typeof selector === 'string' ? document.querySelector(selector) : selector;
        if (element) element.style.display = 'none';
    },

    // Toggle element visibility
    toggle(selector) {
        const element = typeof selector === 'string' ? document.querySelector(selector) : selector;
        if (element) {
            element.style.display = element.style.display === 'none' ? '' : 'none';
        }
    }
};

// Storage utilities
const StorageUtils = {
    // Get item from localStorage
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Storage get error:', error);
            return defaultValue;
        }
    },

    // Set item in localStorage
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Storage set error:', error);
            return false;
        }
    },

    // Remove item from localStorage
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Storage remove error:', error);
            return false;
        }
    },

    // Clear all localStorage
    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Storage clear error:', error);
            return false;
        }
    }
};

// Export utilities
window.Utils = {
    String: StringUtils,
    Date: DateUtils,
    Number: NumberUtils,
    Array: ArrayUtils,
    Url: UrlUtils,
    Api: ApiUtils,
    Dom: DomUtils,
    Storage: StorageUtils
};

// Export commonly used functions directly
window.escapeHtml = StringUtils.escapeHtml;
window.formatDate = DateUtils.formatDate;
window.formatFileSize = NumberUtils.formatFileSize;
window.formatNumber = NumberUtils.formatNumber;
