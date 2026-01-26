# Contact Form / Links Pointing to Wrong Domain (e.g. localchurches.org)

If the contact form link or other links point to `www.localchurches.org` when your app runs on `localchurches.onrender.com`, the cause is usually one of these.

---

## 1. Wagtail Site hostname

**Cause:** The `wagtailcore_site` table has a Site with hostname `www.localchurches.org` (from Heroku). When you visit `localchurches.onrender.com`, Wagtail falls back to that default Site. Any logic that builds full URLs from the Site (redirects, sitemaps, etc.) will use `www.localchurches.org`.

**Fix:** Wagtail Admin → **Settings → Sites** → Add a Site with hostname `localchurches.onrender.com`, same root page as the existing site, port 80 (or 443 if your existing site uses it).

---

## 2. Wagtail Redirects

**Cause:** A redirect from `/contact/` (or another path) to `https://www.localchurches.org/contact/` sends users to the old domain.

**Fix:** Wagtail Admin → **Redirects**. Look for **To:** `https://www.localchurches.org/...`. Delete the redirect or change **To** to a relative path (e.g. `/contact/`).

---

## 3. WAGTAILADMIN_BASE_URL

**Cause:** Used for admin and notification links (e.g. in emails). If it's `https://www.localchurches.org`, those links will point to the old domain.

**Fix:** In **Render Dashboard → Environment**, set `WAGTAILADMIN_BASE_URL=https://localchurches.onrender.com`.

---

## 4. Links in CMS content ("in the text")

**Cause:** A link to `https://www.localchurches.org/contact/` (or the old domain) is stored in CMS fields: rich text (e.g. Contact `intro`), `canonical_url`, `link_external`, GlobalSettings (address links, contact widget text), Advert `url`/`text`, or StreamField body.

**Fix (find and replace in the DB):**

1. **Report only** (see where it appears):
   ```bash
   python manage.py find_wrong_domain_links
   ```

2. **Replace and save** (CharField, TextField, URLField, RichTextField):
   ```bash
   python manage.py find_wrong_domain_links --replace
   ```
   Optional: `--old=www.localchurches.org,localchurches.org` and `--new=localchurches.onrender.com` (these are the defaults).

3. **StreamField / complex blocks:** The command only reports them. Edit those in Wagtail Admin and change or remove the link.

**Manual fix:** In Wagtail, open the Contact page (and any related pages), edit the intro/body or link fields, and replace or remove the old-domain link.

---

## Summary

| Cause            | Fix                                                                 |
|------------------|---------------------------------------------------------------------|
| Wagtail Site     | Add Site for localchurches.onrender.com in Wagtail Admin            |
| Redirects        | Wagtail Admin → Redirects: delete or change **To** to a path        |
| WAGTAILADMIN_BASE_URL | Render → Environment: set to `https://localchurches.onrender.com`  |
| CMS content ("in the text") | `python manage.py find_wrong_domain_links [--replace]`; or edit in Wagtail |
