/* KELP - Key Event Log Parser - Application JavaScript */

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
