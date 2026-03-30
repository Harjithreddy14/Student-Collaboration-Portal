// ── Theme ─────────────────────────────────────────────────
(function() {
  const saved = localStorage.getItem('ch-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateIcon(saved);

  const btn = document.getElementById('themeToggle');
  if (btn) {
    btn.addEventListener('click', function() {
      const current = document.documentElement.getAttribute('data-theme');
      const next    = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('ch-theme', next);
      updateIcon(next);
    });
  }

  function updateIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (!icon) return;
    if (theme === 'dark') {
      icon.className = 'fas fa-sun';
    } else {
      icon.className = 'fas fa-moon';
    }
  }
})();

// ── Auto-dismiss toasts ───────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(function() {
    document.querySelectorAll('.toast.show').forEach(function(t) {
      var toast = bootstrap.Toast.getOrCreateInstance(t);
      toast.hide();
    });
  }, 3500);

  // ── Sticky note color picker ──────────────────────────
  document.querySelectorAll('.color-dot').forEach(function(dot) {
    dot.addEventListener('click', function() {
      const color = this.dataset.color;
      const input = document.getElementById('noteColor');
      if (input) input.value = color;
      document.querySelectorAll('.color-dot').forEach(d => d.classList.remove('selected'));
      this.classList.add('selected');
    });
  });

  // ── Scroll chat to bottom ─────────────────────────────
  var cb = document.getElementById('chatBox');
  if (cb) cb.scrollTop = cb.scrollHeight;
  var dm = document.getElementById('dmMessages');
  if (dm) dm.scrollTop = dm.scrollHeight;

  // ── Todo checkbox toggle ──────────────────────────────
  document.querySelectorAll('.todo-check-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      this.closest('form').submit();
    });
  });

  // ── Confirm delete ────────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(function(el) {
    el.addEventListener('click', function(e) {
      if (!confirm(this.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Select2-like: new DM user search ─────────────────
  const userSearch = document.getElementById('dmUserSearch');
  if (userSearch) {
    userSearch.addEventListener('input', function() {
      const q = this.value.toLowerCase();
      document.querySelectorAll('.dm-user-item').forEach(function(item) {
        const name = item.dataset.name || '';
        item.style.display = name.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }
});
