# Homepage in Wagtail Admin

## Finding the Homepage

The live homepage is the **site root** page. To edit it:

1. **Wagtail Admin → Pages**
2. Open the **root page** at the top of the tree (e.g. "Home" or "The Local Churches").

If you don’t see a page with Homepage fields (disclaimer, info bar, body HTML, etc.), the root may be a generic Page. Run:

```bash
python manage.py ensure_homepage
```

This will create or select a Homepage and set it as the site root so you can edit it in Pages.

---

## What You Edit on the Homepage (Pages → root page)

| Field | Where it appears on the site |
|-------|------------------------------|
| **Title** | Browser tab / SEO |
| **Hero intro** (primary, secondary) | Hero area (if used by template) |
| **Hero** (inline) | Hero links / blocks (if used) |
| **Disclaimer content** | First info bar under the hero (exclamation icon). Leave blank for default text. |
| **Information bar content** | Second info bar after Testimonies (info icon, Bible quote). Leave blank for default. |
| **Blogs tag line** | Heading above Testimonies (e.g. "Real People. Real Stories.") |
| **Body HTML** | Optional. If set, **replaces** the default sections below the hero (disclaimer, testimonies, Bible bar, FAQ, Contact). Leave blank to use the default layout. |
| **Google URL JS / Google key JS** | Used for the hero search (maps) |

---

## Sections That Come From Other Pages

These are **not** stored on the Homepage; they are loaded from other pages. Edit them in **Pages** on the right page.

| Section on homepage | Source | Where to edit |
|--------------------|--------|----------------|
| **FAQ (first 4)** | FAQ index page (slug `faq`) and its FAQ children | **Pages → FAQ** (or the page titled "Frequently Asked Questions"). Add/edit FAQ child pages there. |
| **Contact form** | Contact page (slug `contact`) | **Pages → Contact**. Edit intro text and form fields there. Same form is shown on the homepage. |
| **Testimonies** | Currently hardcoded in the template (four specific testimonies). Tag line comes from Homepage. | Tag line: edit **Blogs tag line** on the Homepage. Changing the four testimonies requires a code/template change unless made dynamic later. |

---

## After Running `ensure_homepage`

- The **root** in **Pages** will be a Homepage (or a child "Home" that is the Homepage).
- The URL `/` will still be the homepage.
- Edit that Homepage in **Pages** to change disclaimer, info bar, tag line, and optional body HTML.
