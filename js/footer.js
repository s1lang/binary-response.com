// footer.js — Single source of truth for Binary Response site footer
(function () {
  var FOOTER_HTML =
    '<div class="footer-grid">' +
    '<div class="footer-brand">' +
    '<a href="/" class="nav-brand"><img src="/img/logo-icon.webp" alt="Binary Response" class="nav-logo" width="32" height="32" fetchpriority="high"><span class="nav-name">Binary Response</span></a>' +
    '<p>Proactive incident response for organisations disclosed on dark web leak sites.</p>' +
    '</div>' +
    '<div class="footer-col"><h4>Services</h4>' +
    '<a href="/services/ir-retainer.html">IR Retainer</a>' +
    '<a href="/services/incident-response.html">Incident Response</a>' +
    '<a href="/services/digital-forensics.html">Digital Forensics</a>' +
    '<a href="/services/malware-analysis.html">Malware Analysis</a>' +
    '<a href="/services/ransomware-negotiations.html">Ransomware Negotiations</a>' +
    '<a href="/services/dark-web-monitoring.html">Dark Web Monitoring</a>' +
    '<a href="/services/dark-web-data-recovery.html">Dark Web Data Recovery</a>' +
    '<a href="/services/tabletop-exercises.html">Tabletop Exercises</a>' +
    '</div>' +
    '<div class="footer-col"><h4>Resources</h4>' +
    '<a href="/resources/how-to-choose-ir-provider.html">How to Choose an IR Provider</a>' +
    '<a href="/resources/ir-retainer-vs-adhoc.html">IR Retainer vs Ad Hoc</a>' +
    '<a href="/resources/what-is-ir-retainer.html">What Is an IR Retainer?</a>' +
    '<a href="/resources/industries-we-serve.html">Industries We Serve</a>' +
    '<a href="/dark-web-alert.html">Dark Web Alert Service</a>' +
    '</div>' +
    '<div class="footer-col"><h4>Company</h4>' +
    '<a href="/about.html">About</a>' +
    '<a href="/threat-intel/">Threat Intel</a>' +
    '<a href="/threat-intel/ransomware-tracker.html">Ransomware Tracker</a>' +
    '<a href="/blog/">Blog</a>' +
    '<a href="/case-studies/">Case Studies</a>' +
    '<a href="/negotiations/">Negotiations</a>' +
    '<a href="/dark-web-alert.html">Dark Web Alert</a>' +
    '<a href="/contact.html">Contact</a>' +
    '</div>' +
    '<div class="footer-col"><h4>Contact</h4>' +
    '<a href="mailto:alerts@binary-response.com" style="color:var(--accent)">&#128680; alerts@binary-response.com</a>' +
    '<a href="mailto:enquiries@binary-response.com">enquiries@binary-response.com</a>' +
    '</div>' +
    '</div>' +
    '<div class="footer-bottom">' +
    '<span>&copy; 2026 Binary Response Ltd.</span>' +
    '<div class="footer-bottom-links">' +
    '<a href="/privacy.html">Privacy</a>' +
    '<a href="/terms.html">Terms</a>' +
    '<a href="/opt-out.html">Opt-Out</a>' +
    '<a href="https://www.linkedin.com/company/binary-response" target="_blank" rel="noopener" aria-label="LinkedIn" style="color:var(--accent);display:inline-flex;align-items:center;gap:0.35rem">' +
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:middle"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>' +
    ' LinkedIn</a>' +
    '</div>' +
    '</div>';

  var el = document.querySelector('.site-footer');
  if (!el) return;
  el.innerHTML = FOOTER_HTML;
}());
