# Master Plan: Fix Wagtail Admin CSS (Admin Page Only)

## Status

- **Phase 1 (done):** Project `static/wagtailadmin/` removed. Admin assets come from the `wagtail` package only.
- **Phase A (done):** `admin_base.html` override had been removed; Phase C adds a minimal override back.
- **Phase B (done):** Compressor safeguard: comments in `production.py` that `wagtailadmin` must not be inside any `{% compress %}` block (django-compressor has no `COMPRESS_EXCLUDE`; the safeguard is documentation).
- **Phase D (done):** `build.sh` verifies `wagtailadmin/css/core.css` in the S3 bucket when S3 is used, and in `STATIC_ROOT` when using WhiteNoise.
- **Phase E (done):** CDN invalidation and hard-refresh note added below (Root cause 6).
- **Phase C (done):** `core.css` returned 200 but styles were not applied (likely `versioned_static` URL or S3 Content-Type). Added `lampstands/core/templates/wagtailadmin/admin_base.html` that uses `{% static 'wagtailadmin/css/core.css' %}` (and `{% static %}` for favicon); JS still uses `{% versioned_static %}`. Extends `wagtailadmin/skeleton.html` and defines `css`, `branding_favicon`, `js` blocks.
- **Current:** Deploy and verify. If still broken: (1) Open the `core.css` URL in a new tab and check the response is real CSS and `Content-Type: text/css`; (2) Invalidate CDN for `wagtailadmin/*` and hard-refresh.

---

## Root causes (prioritised)

### 1. Override drift and unnecessary customisation

Our `admin_base.html` overrides Wagtail’s default. Even if it matches today, it can drift and it adds a needless maintenance surface. Wagtail’s default already loads `core.css` and the right JS in the right order. **Action:** Remove our override and use Wagtail’s default.

### 2. Compressor and admin CSS

- `COMPRESS_OFFLINE = True` and `CompressorFinder` are enabled.
- Admin does **not** use `{% compress %}` for its main CSS; `core.css` is loaded via `{% versioned_static %}`. So Compressor should not be rewriting or merging admin CSS.
- To be safe, we should **exclude** `wagtailadmin` from Compressor so it never touches admin assets. **Action:** Set `COMPRESS_EXCLUDE` (or the appropriate Compressor setting) so `wagtailadmin` is excluded.

### 3. `versioned_static` and S3

- With S3, `versioned_static` typically produces `https://bucket…/wagtailadmin/css/core.css?v=hash`.
- If the tag or storage interaction is wrong, we can get 404s or bad URLs. **Action:** Prefer `{% static 'wagtailadmin/css/core.css' %}` if `versioned_static` keeps 404’ing. (We try `versioned_static` first; only switch if evidence of 404.)

### 4. `core.css` not in S3 / not collected

- If `wagtailadmin/css/core.css` is never uploaded to S3, the link will 404.
- Build runs `collectstatic`. With S3, files go to the bucket; the current check uses `STATIC_ROOT`, which is wrong when using S3. **Action:** When using S3, verify `core.css` via S3 `head_object` or `list_objects` in the build instead of `STATIC_ROOT`.

### 5. Site CSS and hooks

- `villareal-turquoise.css` and other site CSS are in `lampstands` templates; admin uses `wagtailadmin/skeleton` and `admin_base`. They are separate. **No change.**
- `insert_global_admin_css` (FontAwesome, `fix_admin_login_css`) are **disabled**. **No change** until base admin CSS is solid.

### 6. Caching (CDN / browser)

- Old or wrong `core.css` can be served from CDN or browser cache. **Action:** Document that CDN (e.g. CloudFront) should be invalidated for `wagtailadmin/*` after deploys, and that a hard refresh may be needed.

**After deploy:** If admin CSS still looks wrong, invalidate the CDN for `wagtailadmin/*` (e.g. CloudFront invalidation `/wagtailadmin/*`) and do a hard refresh (Cmd+Shift+R / Ctrl+Shift+R) in the browser.

---

## Phases to execute

| Phase | Goal | Action |
|-------|------|--------|
| **A** | Remove override drift | Delete `lampstands/core/templates/wagtailadmin/admin_base.html` so Wagtail’s default is used. |
| **B** | Protect admin from Compressor | Exclude `wagtailadmin` from Compressor (e.g. `COMPRESS_EXCLUDE` or equivalent). |
| **C** | Reliable `core.css` URL | Keep `versioned_static` for now. If 404 continues, add a minimal override that uses `{% static 'wagtailadmin/css/core.css' %}` only. |
| **D** | S3 build check | When S3 is used, in `build.sh` verify `wagtailadmin/css/core.css` in the bucket (not in `STATIC_ROOT`). |
| **E** | Docs | In this file, add: “After deploy, invalidate CDN for `wagtailadmin/*` and hard‑refresh if admin CSS is still wrong.” |

---

## Execution order

1. **A** – Remove `admin_base.html` override.
2. **B** – Exclude `wagtailadmin` from Compressor in production (and base if that’s where finders/compress are shared).
3. **D** – Adjust build verification for S3.
4. **C** – Only if A+B+D are done and admin CSS still 404s: add a minimal `admin_base.html` that uses `{% static 'wagtailadmin/css/core.css' %}` and otherwise inherits from the default.
5. **E** – Update this doc with the CDN/hard‑refresh note.

---

## Rollback

- **A:** Restore `admin_base.html` from git. Our last version matched Wagtail’s default; restoring it is safe.
- **B:** Remove the Compressor exclude.
- **C:** Revert to `versioned_static` in the override, or delete the override again.
- **D:** Revert the `build.sh` verification to the previous `STATIC_ROOT` check (or remove it).

---

## Verification after changes

1. Deploy and open the admin (login and a page edit).
2. DevTools → Network: `wagtailadmin/css/core.css` → status 200, size > 0.
3. Visually: sidebar, header, forms, and modals look correct (no obviously missing or overridden Wagtail styles).
4. If using S3: build logs show that `core.css` was found in the bucket (or in collectstatic output when writing to S3).

## If core.css is 200 but the page is still unstyled

1. **Check the response**: Open the `core.css` URL directly (from the page’s `<link href="...">`). The body must be CSS (starts with `/*` or selectors), not HTML. The response headers should include `Content-Type: text/css`. If it’s HTML or `Content-Type` is wrong, the browser won’t apply it as CSS.
2. **Phase C**: Use `{% static 'wagtailadmin/css/core.css' %}` instead of `{% versioned_static %}` (done in `admin_base.html` override) so the URL has no `?v=hash`; that can avoid S3/CDN serving the wrong object for versioned URLs.
3. **CDN**: Invalidate `wagtailadmin/*` and do a hard refresh (Cmd+Shift+R / Ctrl+Shift+R).
4. **CSP**: If you use `Content-Security-Policy`, ensure `style-src` includes the static origin (e.g. your S3/CloudFront domain) so the browser can load the stylesheet.

---

## References

- `FIX_ADMIN_CSS.md`, `DEBUG_WAGTAIL_ADMIN_CSS.md`, `URGENT_FIX_ADMIN_CSS.md`
- `ROOT_CAUSE_COMMON_JS.md`
- Wagtail 6.4: `wagtail/admin/templates/wagtailadmin/admin_base.html`, `wagtailadmin/skeleton.html`, `wagtail/admin/static/wagtailadmin/css/core.css`
