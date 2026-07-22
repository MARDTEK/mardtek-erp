/* MARDTEK ERP — Alpine.js stores + HTMX config */

// ── Toast notification store ────────────────────────────────────────────
document.addEventListener('alpine:init', () => {
  Alpine.store('toasts', {
    items: [],
    _id: 0,
    add(message, type = 'info', duration = 5000) {
      const id = ++this._id;
      this.items.push({ id, message, type });
      setTimeout(() => this.remove(id), duration);
    },
    remove(id) {
      this.items = this.items.filter(t => t.id !== id);
    }
  });
});

// ── HTMX configuration ─────────────────────────────────────────────────
document.addEventListener('htmx:configRequest', (event) => {
  // Add CSRF token to all HTMX requests
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  if (csrfMeta) {
    event.detail.headers['X-CSRF-Token'] = csrfMeta.content;
  }
});

// ── HTMX error handling ────────────────────────────────────────────────
document.addEventListener('htmx:responseError', (event) => {
  const status = event.detail.xhr.status;
  let message = 'An error occurred';

  if (status === 401) {
    message = 'Session expired. Please log in again.';
    window.location.href = '/login';
    return;
  } else if (status === 403) {
    message = 'You do not have permission for this action.';
  } else if (status === 404) {
    message = 'Resource not found.';
  } else if (status >= 500) {
    message = 'Server error. Please try again.';
  }

  if (typeof Alpine !== 'undefined' && Alpine.store('toasts')) {
    Alpine.store('toasts').add(message, 'error');
  }
});

document.addEventListener('htmx:sendError', () => {
  if (typeof Alpine !== 'undefined' && Alpine.store('toasts')) {
    Alpine.store('toasts').add('Network error. Check your connection.', 'error');
  }
});

// ── HTMX after-request flash messages ──────────────────────────────────
document.addEventListener('htmx:beforeRequest', (event) => {
  const target = event.detail.target;
  if (target) {
    target.classList.add('htmx-loading');
  }
});

document.addEventListener('htmx:afterRequest', (event) => {
  const target = event.detail.target;
  if (target) {
    target.classList.remove('htmx-loading');
  }
});
