document.addEventListener('DOMContentLoaded',()=>{const o=new IntersectionObserver(e=>{e.forEach(el=>{if(el.isIntersecting)el.target.classList.add('visible')})},{threshold:0.1});document.querySelectorAll('.fade-in').forEach(el=>o.observe(el))});

// Mobile nav dropdown toggles
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-dropdown > a').forEach(link => {
    link.addEventListener('click', e => {
      // Only intercept on mobile (when toggle is visible)
      if (window.getComputedStyle(document.querySelector('.nav-toggle')).display === 'none') return;
      e.preventDefault();
      const menu = link.nextElementSibling;
      if (!menu) return;
      // Close other open dropdowns
      document.querySelectorAll('.nav-dropdown-menu.open').forEach(m => {
        if (m !== menu) m.classList.remove('open');
      });
      menu.classList.toggle('open');
    });
  });
  // Close mobile menu when a leaf link is clicked
  document.querySelectorAll('.nav-dropdown-inner a').forEach(a => {
    a.addEventListener('click', () => {
      document.querySelector('.nav-links')?.classList.remove('open');
    });
  });
});
// ── Mobile nav toggle ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      document.querySelector('.nav-links')?.classList.toggle('open');
    });
  }

  // Close menu when any leaf link is tapped on mobile
  document.querySelectorAll('.nav-links > a, .nav-dropdown-inner a').forEach(a => {
    a.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        document.querySelector('.nav-links')?.classList.remove('open');
        document.querySelectorAll('.nav-dropdown-menu').forEach(m => m.classList.remove('open'));
      }
    });
  });
});
