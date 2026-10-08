(function () {
  const banner = document.getElementById('live-banner');
  if (!banner) return;                                   // not shown to users without view permission

  const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
  let delay = 1000;

  function connect() {
    const socket = new WebSocket(`${scheme}://${location.host}/ws/employees/`);

    socket.onopen = () => {
      delay = 1000;
      setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ action: 'ping' }));
      }, 30000);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type !== 'employee') return;
      banner.querySelector('span').textContent = data.message;   // textContent: names are user input
      banner.classList.remove('d-none');
      document.dispatchEvent(new CustomEvent('employee-event', { detail: data }));
    };

    socket.onclose = () => {                              // reconnect with a growing delay
      setTimeout(connect, delay);
      delay = Math.min(delay * 2, 15000);
    };
  }
  connect();
})();