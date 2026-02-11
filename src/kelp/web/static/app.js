/* KELP - Key Event Log Parser - Application JavaScript */

// Theme toggle functionality
function getPreferredTheme() {
    const stored = localStorage.getItem('kelp-theme');
    if (stored) return stored;
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('kelp-theme', theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
}

// Initialize theme on page load
(function() {
    setTheme(getPreferredTheme());
})();

// Filter bar button active state - use event delegation
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.filter-bar button[hx-get*="filter_type"]');
    if (btn) {
        // Remove active from all filter buttons
        document.querySelectorAll('.filter-bar button[hx-get*="filter_type"]').forEach(b => {
            b.classList.remove('active');
        });
        // Add active to clicked button
        btn.classList.add('active');
    }
});

// Copy raw CESR to clipboard
function copyRawCesr(btn) {
    const raw = btn.dataset.raw;
    navigator.clipboard.writeText(raw).then(() => {
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => {
            btn.textContent = originalText;
            btn.classList.remove('copied');
        }, 1500);
    });
}

// jq Editor functions
function toggleJqEditor() {
    const popover = document.getElementById('jq-editor-popover');
    const textarea = document.getElementById('jq-editor-textarea');
    const input = document.querySelector('.jq-filter');
    if (!popover) return;

    const isOpen = popover.classList.toggle('open');
    if (isOpen && textarea && input) {
        textarea.value = input.value;
        textarea.focus();
    }
}

function applyJqFilter() {
    const textarea = document.getElementById('jq-editor-textarea');
    const input = document.querySelector('.jq-filter');
    const popover = document.getElementById('jq-editor-popover');

    if (textarea && input) {
        input.value = textarea.value;
        input.dispatchEvent(new Event('keyup', { bubbles: true }));
    }
    if (popover) {
        popover.classList.remove('open');
    }
}

function clearJqFilter() {
    const textarea = document.getElementById('jq-editor-textarea');
    const input = document.querySelector('.jq-filter');

    if (textarea) textarea.value = '';
    if (input) {
        input.value = '';
        input.dispatchEvent(new Event('keyup', { bubbles: true }));
    }
}

// Close jq editor when clicking outside - use named function to prevent duplicates
function handleJqEditorClickOutside(e) {
    const container = document.querySelector('.jq-editor-container');
    const popover = document.getElementById('jq-editor-popover');
    if (container && popover && !container.contains(e.target)) {
        popover.classList.remove('open');
    }
}

// Initialize once on page load
document.removeEventListener('click', handleJqEditorClickOutside);
document.addEventListener('click', handleJqEditorClickOutside);

// Mode toggle for URL vs Upload
function initModeToggle() {
    const urlBtn = document.querySelector('.mode-btn[data-mode="url"]');
    const uploadBtn = document.querySelector('.mode-btn[data-mode="upload"]');
    const urlForm = document.getElementById('url-form');
    const uploadForm = document.getElementById('upload-form');

    if (!urlBtn || !uploadBtn || !urlForm || !uploadForm) return;

    function switchToUrl() {
        urlBtn.classList.add('active');
        uploadBtn.classList.remove('active');
        urlForm.classList.add('active');
        uploadForm.classList.remove('active');
    }

    function switchToUpload() {
        uploadBtn.classList.add('active');
        urlBtn.classList.remove('active');
        uploadForm.classList.add('active');
        urlForm.classList.remove('active');
    }

    urlBtn.addEventListener('click', function(e) {
        e.preventDefault();
        switchToUrl();
    });

    uploadBtn.addEventListener('click', function(e) {
        e.preventDefault();
        switchToUpload();
    });
}

document.addEventListener('DOMContentLoaded', initModeToggle);

// Reset file input after successful upload
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Clear file input when main content updates (after upload)
    const fileInput = document.getElementById('kel_file');
    if (fileInput) {
        fileInput.value = '';
    }
});

// Also clear on form submission
document.body.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.elt && event.detail.elt.id === 'upload-form') {
        const fileInput = document.getElementById('kel_file');
        if (fileInput && event.detail.successful) {
            fileInput.value = '';
        }
    }
});
