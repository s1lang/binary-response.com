# Binary Response — OpenClaw Blog Integration Guide

## Adding a New Blog Post

To add a new blog post via OpenClaw, two steps are required:

### Step 1: Create the HTML file

Create a new `.html` file in `/blog/posts/` using an existing post as a template.
Copy `blog/posts/ransomware-landscape-q1-2026.html` and modify the content.

Key structure:
- Same nav, footer, and CSS as the rest of the site
- CSS path: `../../css/style.css`
- JS path: `../../js/main.js`  
- Content goes inside `<article class="blog-post-content">...</article>`
- Use `<h2>` for section headings, `<p>` for paragraphs, `<ul><li>` for lists
- Use `<blockquote>` for callout boxes

### Step 2: Update posts.json

Add a new entry to `/blog/posts.json`:

```json
{
  "slug": "your-post-slug",
  "title": "Your Post Title",
  "excerpt": "A 1-2 sentence summary.",
  "date": "2026-03-15",
  "readTime": "5 min read",
  "tag": "threat-intel",
  "tagLabel": "Threat Intelligence"
}
```

### Available Tags

| tag value     | tagLabel            | Colour |
|--------------|---------------------|--------|
| threat-intel | Threat Intelligence | Red    |
| ransomware   | Ransomware          | Amber  |
| advisory     | Advisory            | Green  |
| general      | General             | Grey   |

The blog index page (`blog/index.html`) automatically reads `posts.json` and renders
all posts sorted by date (newest first). No code changes needed.

## Deployment to IONOS

1. Upload the entire folder contents to your web root via IONOS File Manager or FTP
2. Ensure `index.html` is at the root level
3. The site is pure static HTML/CSS/JS — no server-side processing needed
4. Set up DNS redirect from binary-response.co.uk to binary-response.com in IONOS

## File Structure

```
binary-response/
├── index.html                    (Homepage)
├── services.html                 (Services overview)
├── contact.html                  (Contact page with form)
├── about.html                    (About page)
├── css/
│   └── style.css                 (Global stylesheet)
├── js/
│   ├── main.js                   (Shared JS — animations)
│   └── blog.js                   (Blog loader — reads posts.json)
├── img/
│   ├── logo-icon.png             (Shield icon logo)
│   └── logo-full.png             (Full branded logo)
├── services/
│   ├── incident-response.html
│   ├── digital-forensics.html
│   ├── ransomware-negotiations.html
│   ├── dark-web-monitoring.html
│   ├── dark-web-data-recovery.html
│   ├── tabletop-exercises.html
│   ├── security-assessments.html
│   ├── threat-intelligence.html
│   ├── speaking-engagements.html
│   ├── expert-witness.html
│   └── breach-notification.html
├── blog/
│   ├── index.html                (Blog listing — auto-loads from posts.json)
│   ├── posts.json                (Blog metadata — UPDATE THIS)
│   └── posts/                    (Individual posts — ADD FILES HERE)
│       ├── ransomware-landscape-q1-2026.html
│       ├── first-72-hours-ransomware.html
│       └── sanctions-screening-ransom-payments.html
└── OPENCLAW-BLOG-GUIDE.md        (This file)
```

## Contact Form

The contact form on contact.html uses FormSubmit.co as a free form backend.
To configure it:
1. Replace `info@binary-response.com` in the form action URL with your email
2. First submission will trigger a verification email from FormSubmit
3. After verification, all form submissions go directly to your inbox

Alternatively, replace the form action with your preferred form handler.
