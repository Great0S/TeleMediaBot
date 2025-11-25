// ==================== Reusable UI Components ====================

// Toast Notifications
const Toast = {
    container: null,

    init() {
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },

    show(message, type = 'info', duration = 3000) {
        this.init();

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = this.getIcon(type);
        toast.innerHTML = `
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${message}</span>
        `;

        this.container.appendChild(toast);

        // Auto remove
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);

        return toast;
    },

    getIcon(type) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    },

    success(message, duration) {
        return this.show(message, 'success', duration);
    },

    error(message, duration) {
        return this.show(message, 'error', duration);
    },

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    },

    info(message, duration) {
        return this.show(message, 'info', duration);
    }
};

// Modal Component
const Modal = {
    container: null,

    init() {
        this.container = document.getElementById('modal-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'modal-container';
            this.container.className = 'modal-container';
            document.body.appendChild(this.container);
        }
    },

    show(options = {}) {
        this.init();

        const {
            title = 'Modal',
            content = '',
            buttons = [{ text: 'Close', onClick: () => this.hide() }],
            onClose = null
        } = options;

        const modal = document.createElement('div');
        modal.className = 'modal';

        const buttonsHtml = buttons.map((btn, index) => {
            const btnClass = btn.primary ? 'btn-primary' : 'btn-secondary';
            return `<button class="btn ${btnClass}" data-index="${index}">${btn.text}</button>`;
        }).join('');

        modal.innerHTML = `
            <div class="modal-header">
                <h3 class="modal-title">${title}</h3>
                <button class="modal-close" aria-label="Close">×</button>
            </div>
            <div class="modal-body">${content}</div>
            <div class="modal-footer">
                ${buttonsHtml}
            </div>
        `;

        this.container.innerHTML = '';
        this.container.appendChild(modal);
        this.container.classList.add('active');

        // Event handlers
        modal.querySelector('.modal-close').addEventListener('click', () => {
            this.hide();
            if (onClose) onClose();
        });

        modal.querySelectorAll('.modal-footer .btn').forEach((btn, index) => {
            btn.addEventListener('click', () => {
                if (buttons[index].onClick) {
                    buttons[index].onClick();
                }
            });
        });

        // Close on backdrop click
        this.container.addEventListener('click', (e) => {
            if (e.target === this.container) {
                this.hide();
                if (onClose) onClose();
            }
        });

        return modal;
    },

    hide() {
        if (this.container) {
            this.container.classList.remove('active');
        }
    },

    confirm(message, onConfirm, onCancel) {
        return this.show({
            title: 'Confirm',
            content: `<p>${message}</p>`,
            buttons: [
                { text: 'Cancel', onClick: () => { this.hide(); if (onCancel) onCancel(); } },
                { text: 'Confirm', primary: true, onClick: () => { this.hide(); if (onConfirm) onConfirm(); } }
            ]
        });
    }
};

// Loading Overlay
const Loading = {
    overlay: null,

    init() {
        this.overlay = document.getElementById('loading-overlay');
        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.id = 'loading-overlay';
            this.overlay.className = 'loading-overlay';
            this.overlay.innerHTML = '<div class="spinner-large"></div>';
            document.body.appendChild(this.overlay);
        }
    },

    show() {
        this.init();
        this.overlay.style.display = 'flex';
    },

    hide() {
        if (this.overlay) {
            this.overlay.style.display = 'none';
        }
    }
};

// Dropdown Component
function initDropdowns() {
    document.addEventListener('click', (e) => {
        const trigger = e.target.closest('[data-dropdown-trigger]');

        if (trigger) {
            const menuId = trigger.dataset.dropdownTrigger;
            const menu = document.getElementById(menuId);

            if (menu) {
                menu.classList.toggle('active');
                e.stopPropagation();
            }
        } else {
            // Close all dropdowns when clicking outside
            document.querySelectorAll('.dropdown-menu.active').forEach(menu => {
                menu.classList.remove('active');
            });
        }
    });
}

// Tabs Component
function initTabs() {
    document.querySelectorAll('[data-tab]').forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.dataset.tab;
            const tabGroup = tab.closest('[data-tab-group]');

            if (!tabGroup) return;

            // Deactivate all tabs and contents in this group
            tabGroup.querySelectorAll('[data-tab]').forEach(t => t.classList.remove('active'));
            tabGroup.querySelectorAll('[data-tab-content]').forEach(c => c.classList.remove('active'));

            // Activate clicked tab and its content
            tab.classList.add('active');
            const content = tabGroup.querySelector(`[data-tab-content="${targetId}"]`);
            if (content) {
                content.classList.add('active');
            }
        });
    });
}

// Copy to Clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        Toast.success('Copied to clipboard');
        return true;
    } catch (err) {
        console.error('Failed to copy:', err);
        Toast.error('Failed to copy to clipboard');
        return false;
    }
}

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize all components
document.addEventListener('DOMContentLoaded', () => {
    initDropdowns();
    initTabs();

    // Initialize copy buttons
    document.addEventListener('click', async (e) => {
        const copyBtn = e.target.closest('[data-copy]');
        if (copyBtn) {
            const text = copyBtn.dataset.copy;
            await copyToClipboard(text);
        }
    });
});

// Export components for global use
window.Toast = Toast;
window.Modal = Modal;
window.Loading = Loading;
window.copyToClipboard = copyToClipboard;
window.debounce = debounce;
