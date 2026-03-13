// nav.js — Single source of truth for Binary Response site navigation
// Runs synchronously at end of <body>, before main.js event listeners attach.
(function () {
  var NAV_HTML =
    '<a href="/">Home</a>' +
    '<div class="nav-dropdown"><a href="/services.html">Services &#9662;</a>' +
    '<div class="nav-dropdown-menu"><div class="nav-dropdown-inner">' +
    '<a href="/services/ir-retainer.html">IR Retainer</a>' +
    '<a href="/services/incident-response.html">Incident Response</a>' +
    '<a href="/services/digital-forensics.html">Digital Forensics</a>' +
    '<a href="/services/malware-analysis.html">Malware Analysis</a>' +
    '<a href="/services/ransomware-negotiations.html">Ransomware Negotiations</a>' +
    '<a href="/services/dark-web-monitoring.html">Dark Web Monitoring</a>' +
    '<a href="/services/dark-web-data-recovery.html">Dark Web Data Recovery</a>' +
    '<a href="/services/tabletop-exercises.html">Tabletop Exercises</a>' +
    '<a href="/services/security-assessments.html">Security Assessments</a>' +
    '<a href="/services/threat-intelligence.html">Threat Intelligence</a>' +
    '<a href="/services/cyber-insurance-support.html">Cyber Insurance Support</a>' +
    '<a href="/services/cyber-due-diligence.html">M&amp;A Cyber Due Diligence</a>' +
    '<a href="/services/speaking-engagements.html">Professional Speaking</a>' +
    '<a href="/services/expert-witness.html">Expert Witness Services</a>' +
    '<a href="/services/breach-notification.html">Breach Notification Support</a>' +
    '<a href="/dark-web-alert.html">Dark Web Alert</a>' +
    '</div></div></div>' +
    '<a href="/threat-intel/">Threat Intel</a>' +
    '<a href="/threat-intel/ransomware-tracker.html">Ransomware Tracker</a>' +
    '<a href="/blog/">Blog</a>' +
    '<a href="/case-studies/">Case Studies</a>' +
    '<a href="/negotiations/">Negotiations</a>' +
    '<div class="nav-dropdown"><a href="/for/">Industries &#9662;</a>' +
    '<div class="nav-dropdown-menu"><div class="nav-dropdown-inner">' +
    '<a href="/for/healthcare.html">Healthcare</a>' +
    '<a href="/for/legal.html">Legal</a>' +
    '<a href="/for/manufacturing.html">Manufacturing</a>' +
    '<a href="/for/financial-services.html">Financial Services</a>' +
    '<a href="/for/education.html">Education</a>' +
    '</div></div></div>' +
    '<a href="/resources/">Resources</a>' +
    '<a href="/about.html">About</a>' +
    '<a href="/team.html">Our Team</a>' +
    '<a href="/careers.html">Careers</a>' +
    '<a href="/contact.html" class="nav-cta">Get Help Now</a>';

  var el = document.querySelector('.nav-links');
  if (!el) return;

  el.innerHTML = NAV_HTML;

  // Set active state
  var path = window.location.pathname.replace(/\/index\.html$/, '/');
  if (path === '') path = '/';

  el.querySelectorAll('a').forEach(function (a) {
    if (a.classList.contains('nav-cta')) return;
    // Don't mark dropdown inner items as active
    if (a.closest('.nav-dropdown-inner')) return;

    var h = a.getAttribute('href');
    if (!h) return;

    var active = false;

    if (h === '/') {
      active = (path === '/' || path === '/index.html');
    } else if (h === '/threat-intel/ransomware-tracker.html') {
      active = path === '/threat-intel/ransomware-tracker.html';
    } else if (h === '/threat-intel/') {
      active = path.startsWith('/threat-intel/') && path !== '/threat-intel/ransomware-tracker.html';
    } else if (h === '/services.html') {
      active = path.startsWith('/services');
    } else if (h === '/for/') {
      active = path.startsWith('/for/');
    } else if (h === '/negotiations/') {
      active = path.startsWith('/negotiations/');
    } else if (h === '/resources/') {
      active = path.startsWith('/resources/');
    } else {
      var base = h.replace(/index\.html$/, '');
      active = path.startsWith(base) || path === h;
    }

    if (active) a.classList.add('active');
  });
}());
