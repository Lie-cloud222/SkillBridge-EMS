(function () {
  const el = (id) => document.getElementById(id);

  async function refreshStats() {
    try {
      const response = await fetch('/api/v1/employees/stats/', {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      });
      if (!response.ok) return;
      const stats = await response.json();
      el('stat-total').textContent = stats.total;
      el('stat-active').textContent = stats.active;
      el('stat-inactive').textContent = stats.inactive;
      const list = el('stat-departments');
      list.replaceChildren();
      Object.entries(stats.by_department).forEach(([name, count]) => {
        const item = document.createElement('li');
        item.textContent = `${name}: ${count}`;
        list.appendChild(item);
      });
    } catch (error) {
      console.error('Could not refresh stats', error);
    }
  }

  document.addEventListener('employee-event', (event) => {
    const empty = el('activity-empty');
    if (empty) empty.remove();
    const item = document.createElement('li');
    item.textContent = `${new Date().toLocaleTimeString()}  ${event.detail.message}`;
    el('activity').prepend(item);
    refreshStats();
  });
})();