# Keeping organization detail URLs unreachable while published

Organization listing **entry** pages (e.g. [Defense & Confirmation Project](https://localchurches.org/organizations-listing/dcp/)) can be kept **published** (live) but **not reachable** by bots or direct URL traversal.

## Option 1: Middleware (current implementation)

**What it does:** `BlockOrganizationDetailMiddleware` returns **403 Forbidden** (and `X-Robots-Tag: noindex, nofollow`) for GET requests to organization **detail** URLs like `/organizations-listing/dcp/`. The org **index** (`/organizations-listing/`) is not blocked.

**Result:**
- Pages stay **published** (live).
- They still appear in the org listing and in the Wagtail API (because there is no Wagtail view restriction).
- Visiting the detail URL (or a bot crawling it) gets 403 and no content; search engines are told not to index it.

**Settings:**
- `BLOCK_ORGANIZATION_DETAIL_URLS = True` (default in `lampstands/settings/base.py`) — blocking is on.
- Set to `False` to allow normal access to org detail URLs again.

**To disable:** In your environment or in a settings override, set:
```python
BLOCK_ORGANIZATION_DETAIL_URLS = False
```

---

## Option 2: Wagtail Privacy (view restriction)

If you **do not** need org pages to appear in the org listing or in the API for anonymous users, you can use Wagtail’s built-in **Privacy** (view restriction) on the page or its parent:

1. In the Wagtail admin, open the organization page (or the “Organizations listing” parent).
2. In **Privacy**, choose e.g. **“Accessible with a shared password”** or **“Accessible to logged-in users”**.
3. Save.

**Result:**
- Page stays **published** (live).
- Direct visits to the URL get a password/login form; without it, no content is shown (good for bots and URL traversal).
- The page is **excluded** from `.public()` and from the Wagtail API for unauthenticated requests, so it will **not** appear in the org listing or in the public API.

Use this when you are fine with the org not being listed publicly and only want access via password/login.

---

## Summary

| Goal | Option 1 (Middleware) | Option 2 (Wagtail Private) |
|------|------------------------|----------------------------|
| Page stays published | Yes | Yes |
| URL not reachable (no content) | Yes (403) | Yes (password/login) |
| Still in org listing | Yes | No |
| Still in API (anon) | Yes | No |
| Bots / crawlers | 403 + noindex | Login/password form |

For “published, listed, and in API but URL not reachable,” use **Option 1** (middleware). For “published but only with password and not in listing/API,” use **Option 2** (Wagtail Privacy).
