# Master Plan: Fix Wagtail Admin CSS (Permanently)

## Why previous fixes failed (3+ attempts)

1. **Conflicting sources** – Admin static comes from two places: project `static/wagtailadmin/` (old, from an older Wagtail build) and the `wagtail` package. `FileSystemFinder` runs first, so the project copy wins and overrides the package. That mix (old `core.css`/`common.js`/`wagtailadmin.js` + newer `vendor.js`/jQuery from the package) causes broken layout and JS errors.

2. **Targeting symptoms** – Past fixes focused on 404s, collectstatic, S3, `versioned_static`, and disabling CSS hooks. The underlying issue is **which** `core.css` and JS are used, not just that *some* files load.

3. **Over-customisation** – `admin_base.html` was fully overridden and references a specific, old set of files (e.g. `common.js`). The `wagtail` 6.4 package uses a different build; our override locks us into an old build that we keep in `static/wagtailadmin/`.

---

## Root cause (one-line)

**Project `static/wagtailadmin/` overrides the Wagtail package’s admin static. That project copy is from an older build and clashes with Wagtail 6.4.**

---

## Plan overview

| Phase | Goal | Risk |
|-------|------|------|
| **1** | Stop using project `static/wagtailadmin/` as source so admin uses only the package | Need to align `admin_base.html` with what the package provides |
| **2** | Simplify `admin_base.html` to the minimum override (ideally only `common.js` if still needed) | May need to drop `common.js` if package build no longer needs it |
| **3** | Confirm `versioned_static` and S3/WhiteNoise; no front-end CSS in admin | Low |
| **4** | Optional: re-enable `insert_global_admin_css` hooks (FontAwesome, login tweaks) only after 1–3 are stable | Medium |

---

## Phase 1: Stop using project `static/wagtailadmin/` as source

### 1.1 Why this helps

- **Finder order:** `FileSystemFinder` (uses `STATICFILES_DIRS` = `static/`) runs before `AppDirectoriesFinder`. For `wagtailadmin/css/core.css`, the project’s `static/wagtailadmin/css/core.css` is chosen; the package’s is never used.
- **What the project has:** Old `core.css`, `common.js`, `wagtailadmin.js`, `core.js`, jquery 2.2.1, jquery-ui 1.10.3, Hallo, etc. Wagtail 6.4 uses a different admin build (different `core.css`, different JS layout).
- **Mismatch:** `admin_base.html` asks for `jquery-3.6.0`, `jquery-ui-1.13.2`, `vendor.js` (which the project does not have) → those come from the package. `core.css`, `common.js`, `wagtailadmin.js`, `core.js` come from the project. Mixed origins → broken CSS and possible JS errors.

### 1.2 What to do

**Remove `static/wagtailadmin/` from the project** so that all `wagtailadmin/*` assets are resolved from the `wagtail` package via `AppDirectoriesFinder`.

- **Option A (recommended):** Delete the `static/wagtailadmin/` directory from the repo.
- **Option B:** Move it to e.g. `static/_archived/wagtailadmin/` or out of `static/` so it is no longer under `STATICFILES_DIRS`. Same effect for finders.

### 1.3 `admin_base.html` and `common.js`

- Our `admin_base.html` explicitly includes `wagtailadmin/js/common.js`. The Wagtail 6.4 default `admin_base` does **not** include `common.js`; its build inlines the runtime. Our `wagtailadmin.js` in the project was built to use `webpackJsonp` from `common.js`.
- **After Phase 1:** `common.js` and `wagtailadmin.js` will come from the **package**. The package’s `wagtailadmin.js` may not use `webpackJsonp`; if so, loading `common.js` is unnecessary and can be removed from the override.
- **Action:** After deleting `static/wagtailadmin/`, test admin. If the package’s `admin_base` works with no `common.js`, we can **replace our full `admin_base` override with Wagtail’s default** (Phase 2). If `webpackJsonp` errors appear, keep only the `common.js` line in an otherwise minimal override; if the package has no `common.js`, we must either stay with a custom build or upgrade the way we include admin JS.

### 1.4 Rollback

- Restore `static/wagtailadmin/` from git and redeploy. Admin will revert to the previous (broken but familiar) mix.

---

## Phase 2: Simplify `admin_base.html`

### 2.1 Goal

- Use Wagtail’s default `admin_base.html` and blocks if possible.
- If we must override, limit the override to the minimum: e.g. one extra `<script>` for `common.js` only if the package’s `wagtailadmin.js` still expects it.

### 2.2 Steps

1. Remove our `lampstands/core/templates/wagtailadmin/admin_base.html` and test with the default.
2. If that works: done. If `webpackJsonp` (or similar) appears: add a minimal override that only inserts `common.js` before `wagtailadmin.js`, and keep the rest as in the default.
3. Periodically diff our `admin_base` against upstream Wagtail 6.4 to avoid drift.

---

## Phase 3: `versioned_static`, S3/WhiteNoise, and pollution

### 3.1 `versioned_static` and 404s

- If `{% versioned_static 'wagtailadmin/css/core.css' %}` produces hashed paths that 404 on S3, try `{% static 'wagtailadmin/css/core.css' %}` for core admin assets. Prefer `versioned_static` when it works.

### 3.2 Front-end CSS in admin

- Ensure `villareal-turquoise.css` and other site CSS are **not** loaded in admin. Our current `admin_base` does not include them; keep it that way.

### 3.3 Compressor

- `COMPRESS_OFFLINE = True` and `CompressorFinder` should not process Wagtail admin bundles; Wagtail uses its own build. If admin CSS breaks after Compressor changes, exclude `wagtailadmin` from Compressor.

---

## Phase 4 (optional): Re-enable `insert_global_admin_css` hooks

- In `wagtail_hooks.py`, `import_fontawesome_stylesheet` and `fix_admin_login_css` are disabled.
- Re-enable only after Phases 1–3 are stable. Use scoped selectors (e.g. `body.login` for login tweaks) so they don’t affect the main admin.

---

## Diagnostics (before and after each phase)

### Which `core.css` is used

- In browser DevTools → Network: open the URL for `core.css` (e.g. `.../wagtailadmin/css/core.css?...`). If it’s from the package, the path and optional hash should match what’s in the installed `wagtail` package.

### 404s

- Network tab: filter by “css” and “js”; ensure no 404s for `wagtailadmin/` assets.

### collectstatic

- Build logs: confirm lines like  
  `Copying '.../site-packages/wagtail/.../static/wagtailadmin/...'`  
  for `core.css` and key JS. After Phase 1, there should be **no** “Copying” from `static/wagtailadmin/` (project).

### Finder order (optional)

```python
from django.contrib.staticfiles.finders import get_finders
for finder in get_finders():
    # Manually resolve 'wagtailadmin/css/core.css' to see which finder and path wins
```

---

## Summary

| What | Before | After (Phase 1) |
|------|--------|------------------|
| `wagtailadmin/css/core.css` | From `static/wagtailadmin/` (project) | From `wagtail` package |
| `wagtailadmin/js/common.js` | From project | From package (or dropped in Phase 2 if not needed) |
| `wagtailadmin/js/wagtailadmin.js` | From project | From package |
| Other `wagtailadmin/*` | Mix of project + package | All from package |

Phase 1 is the necessary change; Phases 2–4 clean up and harden it.

---

## Files to touch

- **Phase 1:** Remove or relocate `static/wagtailadmin/` (and update `.gitignore` if it’s now ignored or archived).
- **Phase 2:** `lampstands/core/templates/wagtailadmin/admin_base.html` – delete or reduce to a minimal override.
- **Phase 4:** `lampstands/core/wagtail_hooks.py` – uncomment and adjust the `insert_global_admin_css` hooks when safe.

---

## Phase 1 implementation (done)

- **`static/wagtailadmin/`** – Removed from the project. All `wagtailadmin/*` assets now come from the `wagtail` package via `AppDirectoriesFinder`.
- **`admin_base.html`** – The `<script src="...common.js">` line was removed. The Wagtail 6.4 package does not ship `common.js` (runtime is inlined in its `wagtailadmin.js`). Keeping it would 404. If you see `webpackJsonp is not defined` after deploy, the next step is Phase 2: replace our `admin_base` with Wagtail’s default.

---

## References

- `ROOT_CAUSE_COMMON_JS.md` – why `common.js` was added to `admin_base`
- `FIX_ADMIN_CSS.md`, `DEBUG_WAGTAIL_ADMIN_CSS.md`, `URGENT_FIX_ADMIN_CSS.md` – 404s, collectstatic, S3
