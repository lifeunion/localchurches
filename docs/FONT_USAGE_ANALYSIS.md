# Font Usage Analysis

Analysis of fonts (family and size) used across the repository, with the page/section where each applies. Primary source: `static/css/villareal-turquoise.css` and templates.

---

## Side-by-side: Font | Size | Page/Section

| Font family | Font size | Page / Section |
|-------------|-----------|----------------|
| **Global / base** |
| sans-serif (html fallback) | — | Root / all pages |
| **'Raleway', 'Arial', sans-serif** | **0.95em** (base) | **Body – site-wide** (all pages) |
| **'Raleway', 'Arial', sans-serif** | **1.4em** | **Paragraphs (p)** – general content |
| **serif** | **1.5em** | **Blockquotes** – quote blocks |
| **serif** | **0.7em** | **Blockquote cite** – attribution |
| **'Helvetica Neue', Helvetica, Arial, sans-serif** | 1rem | Bootstrap base (overridden by body above on main theme) |
| **Headings (Bootstrap / theme)** |
| inherit | 2.5rem (h1) | Generic h1 |
| inherit | 2rem (h2) | Generic h2 |
| inherit | 1.75rem (h3) | Generic h3 |
| inherit | 1.5rem (h4) | Generic h4 |
| inherit | 1.25rem (h5) | Generic h5 |
| inherit | 1rem (h6) | Generic h6 |
| **Header** |
| Raleway (inherited) | 2em | **.header-logo** – “the local churches” (desktop) |
| Raleway (inherited) | 1.5em | **.header-small .header-logo** – logo when header is small |
| Raleway (inherited) | 1.1em | **.header-search .form-control** – header search input |
| Raleway (inherited) | 3.4em | **.header-information .fa** – header info icons |
| Raleway (inherited) | 1.25em | **.header-information strong** |
| Raleway (inherited) | 0.9em | **.header-information span** |
| Raleway (inherited) | 0.85em | **.header-topbar**, **.header-action** |
| **Navigation** |
| Raleway (inherited) | 16px | **.bleed li a** – nav links (mobile) |
| Raleway (inherited) | 14px | **.bleed li a** – nav links (≥768px) |
| **Cover / hero (homepage)** |
| Raleway (inherited) | 3.6em | **.cover-title-inner h1** – “Find a local church.” |
| Raleway (inherited) | 2.5em | **.cover-title-inner h1** @ ≤991px |
| Raleway (inherited) | 2.2em | **.cover-title-inner h1** @ ≤767px |
| Raleway (inherited) | 2em | **.cover-title-inner h1** @ ≤543px |
| Raleway (inherited) | 1.5em | **.cover-title-inner strong** |
| Raleway (inherited) | 1.25em | **.cover-title-inner p** |
| Raleway (inherited) | 1.05em | **.cover .form-control** – hero search input |
| Raleway (inherited) | 0.9em | **.cover-title-text**, **.cover-title-action**, **.cover-title-action .fa** @ ≤543px |
| **Content title (page banners, e.g. List of Churches)** |
| Raleway (inherited) | 3.1em | **.content-title h1** – page title in gradient bar |
| **Page header (section titles, e.g. “Real People. Real Stories.”, FAQ, Contact Us)** |
| Raleway (inherited) | 3em | **.page-header h1** |
| Raleway (inherited) | 2em | **.page-header h1** @ ≤767px |
| Raleway (inherited) | 2em | **.page-header h2** |
| Raleway (inherited) | 0.85rem | **.page-header h2 ul** |
| Raleway (inherited) | 1.3em | **.page-header h3** |
| Raleway (inherited) | 1.2em | **.page-header p**, **.page-header ul** |
| Raleway (inherited) | 0.9em | **.page-header ul li** @ ≤767px |
| Raleway (inherited) | 1.5em | **.page-header ul li:after** (slash separator) |
| **Information bar (disclaimer / Bible quote bars)** |
| Raleway (inherited) | 1.5em | **.information-bar** – bar text |
| Raleway (inherited) | 1.25em | **.information-bar .fa** – icon |
| **Disclaimer (map / churches list)** |
| Raleway (inherited) | 0.95em | **.church-list-note** (CSS) – disclaimer under toggle |
| Raleway (inherited) | 0.95em | **Map page disclaimer** (inline) – same text |
| **Listing boxes (testimonies, cards)** |
| Raleway (inherited) | 1.9em | **.listing-box-image-title h2** – main title on image |
| Raleway (inherited) | 1.3em | **.listing-box-image-title h3** – subtitle on image |
| Raleway (inherited) | 1.5em | **.listing-box-title h2** – title in grey/teal bar |
| Raleway (inherited) | 1.1em | **.listing-box-title h3** |
| Raleway (inherited) | 0.95em | **.listing-box-content** – body text |
| Raleway (inherited) | 1em | **.listing-box-content p** |
| Raleway (inherited) | 14px | **.listing-box-content p .fa** |
| **FAQ** |
| Raleway (inherited) | 1.25em | **.faq-item:before** – “Q” badge |
| Raleway (inherited) | 1.6em | **.faq-item-question h2** – question text |
| (inherited) | (inherited) | **.faq-item-answer** – answer (color gray) |
| **Pagination** |
| Raleway (inherited) | 1.25em | **.page-link** – pagination links |
| **Footer** |
| Raleway (inherited) | 14px | **.footer-wrapper .btn** |
| Raleway (inherited) | 1.5em | **.footer-top h2** |
| Raleway (inherited) | 0.95em | **.footer-top p** |
| **Contact form** |
| Raleway (inherited) | 1rem | **.form-control** – inputs (global) |
| (inherited) | (inherited) | **.listing-contact-form .contact-form-intro** – gray intro text |
| **Mobile icon bar (bottom nav)** |
| **sans-serif** | **small** | **Icon bar labels** – “Find Us”, “Testimonies”, “Beliefs”, “Recognition”, “History” (inline in base.html, base_blog.html, map_page.html) |
| Raleway (inherited) | 20px | **.icon-bar a** – icon area |
| Raleway (inherited) | 1.7em | **.top-mobile-icon** – top mobile icons |
| **Other UI** |
| Raleway (inherited) | 1.1em | **.header-search .form-control** |
| **'FontAwesome'** | 1em, 0.6em, etc. | **Icons** – .fa, nav icons, listing icons, etc. |
| **Menlo, Monaco, Consolas, 'Courier New', monospace** | 90% | **code** (Bootstrap) |
| **serif** | 30px | **.carousel-control .icon-next** (chevron) |
| **Verdana** | 97.96px | **Logo SVG** – lampstands_logo.html (inline) |
| **system-ui, -apple-system, sans-serif** | — | **Wagtail admin** – admin_base.html |

---

## Summary

- **Primary typeface:** **Raleway** (with Arial and sans-serif fallback) for almost all site content; loaded via `@font-face` in `villareal-turquoise.css`.
- **Base size:** **0.95em** on `body` (with `html { font-size: 16px }`), so 1em ≈ 15.2px.
- **Secondary:** **serif** for blockquotes and some accents; **sans-serif** for mobile icon bar labels; **FontAwesome** for icons; **Verdana** in one logo SVG; **system-ui** in Wagtail admin only.
- **Sections with largest type:** Hero “Find a local church.” (3.6em → 2em responsive), content-title (3.1em), page-header h1 (3em / 2em), information bar (1.5em), listing-box image titles (1.9em / 1.3em).

---

## Where it’s defined

- **Global / theme:** `static/css/villareal-turquoise.css` (and noncompressed variant): body, headings, Raleway `@font-face`, header, cover, page-header, information-bar, listing-box, FAQ, footer, etc.
- **Bootstrap base:** Same file (and Bootstrap source): html, body fallback, h1–h6, .form-control, .btn, .dropdown, etc., before theme overrides.
- **Template-level:**  
  - **Map / churches disclaimer:** `church-list-note` (0.95em) in CSS; map page also has inline `font-size: 0.95em`.  
  - **Mobile icon bar labels:** `style="font-size: small; font-family: sans-serif;"` in `base.html`, `base_blog.html`, `map_page.html`.  
  - **Churches list:** `.church-list-note` and expand icon (e.g. `font-size: 1.5em`) in `church_index_page.html`.  
  - **Logo:** `lampstands_logo.html` inline SVG (Verdana, 97.96px).  
  - **Wagtail admin:** `admin_base.html` (system-ui, -apple-system, sans-serif).
