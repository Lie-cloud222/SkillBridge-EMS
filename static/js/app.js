// app.js - small behaviour for SkillBridge EMS
document.addEventListener('DOMContentLoaded', () => {

  // 1. Success and info messages (from Django's messages framework) fade out after 5 seconds.
  //    Error messages stay on screen until the user closes them.
  document.querySelectorAll('.alert-success, .alert-info').forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });

  // 2. Any element marked data-confirm asks "Are you sure?" before it is followed or submitted.
  //    Example: <a href="..." data-confirm="Delete this employee?">
  document.querySelectorAll('[data-confirm]').forEach((element) => {
    element.addEventListener('click', (event) => {
      if (!window.confirm(element.dataset.confirm)) {
        event.preventDefault();
      }
    });
  });

});