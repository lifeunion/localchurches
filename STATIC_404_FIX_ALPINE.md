# Fix for Static 404s and MIME Type Errors (alpine-modernization)

## Summary of Errors Fixed

- **MIME type 'text/html'** for CSS/JS: Django's 404 page (HTML) was returned when static files were missing; browsers reject HTML as stylesheet/script.
- **404 (Not Found)** for: `villareal-turquoise.css`, `font-awesome.min.css`, `tether.min.js`, `bootstrap.min.js`, `owl.carousel.min.js`, `jquery.min.js`, `jquery1.7.1googapi.min.js`, `jquery.geocomplete.min.js`, `bluemap.jpg`, `vessel1.jpg`.
- **`$ is not defined`**: jQuery failed to load due to 404s, so `initHomePageGeocomplete` threw.

## Root Cause (Hypothesis)

1. **`CompressedStaticFilesStorage`** (used in staging) runs a `post_process` step during `collectstatic` that can fail or skip files on some environments (e.g. missing brotli/gzip tooling or path edge cases on Render). That led to some files not being written to `STATIC_ROOT`.
2. **WhiteNoise** could not find those files and passed the request through to Django, which returned its 404 HTML page → "MIME type ('text/html') is not a supported stylesheet MIME type".
3. **jQuery 404** → `$` undefined when the Maps callback ran.

## Changes Made

### 1. `lampstands/settings/staging.py`

- **Switched `STATICFILES_STORAGE`** from `whitenoise.storage.CompressedStaticFilesStorage` to `django.contrib.staticfiles.storage.StaticFilesStorage`.
- **Reason**: Avoid `post_process` and compression during `collectstatic` so all files are reliably written to `STATIC_ROOT`. WhiteNoise still gzips responses on the fly.
- **`STORAGES["staticfiles"]`** updated to match.

### 2. `build.sh`

- **Verification** when not using S3 now includes all previously 404’ing assets:
  - `js/villareal/tether.min.js`, `bootstrap.min.js`, `jquery.geocomplete.min.js`, `jquery1.7.1googapi.min.js`
  - `css/libraries/owl-carousel/owl.carousel.min.js`
  - `css/img/bluemap.jpg`, `css/img/vessel1.jpg`
- **Reason**: If `collectstatic` doesn’t put these into `STATIC_ROOT`, the build fails instead of deploying with 404s.

### 3. `lampstands/core/templates/lampstands/base.html`

- **jQuery CDN fallback** after the main jQuery script:
  - If `window.jQuery` is undefined (e.g. our `jquery.min.js` 404’d), we load `https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js`.
- **Reason**: Reduces impact of jQuery 404 and helps avoid `$ is not defined`.

### 4. `lampstands/core/templates/lampstands/home_page.html`

- **Guard in `initHomePageGeocomplete`**: `if (typeof $ === 'undefined') { return; }` before using `$`.
- **Reason**: Prevents `ReferenceError: $ is not defined` if both our jQuery and the CDN fallback fail.

## How to Verify on Render

1. **Deploy** the `alpine-modernization` branch (or a branch with these changes).
2. **Build logs**:
   - Look for: `DJANGO_SETTINGS_MODULE=lampstands.settings.staging`
   - `collectstatic` should complete without errors.
   - Verification block should show:
     - `✅ Site theme CSS`
     - `✅ Font Awesome`
     - `✅ jQuery`, `✅ Tether`, `✅ Bootstrap`, `✅ Owl Carousel`, `✅ jQuery Geocomplete`, `✅ jQuery 1.7.1 Google API`, `✅ Bluemap image`, `✅ Vessel1 image`
   - If any show `❌ ... NOT found`, the build will fail; fix `collectstatic` / `STATICFILES_DIRS` before deploying.
3. **Browser** at `https://<your-render-url>/`:
   - DevTools → Network: `villareal-turquoise.css`, `font-awesome.min.css`, `jquery.min.js`, `tether.min.js`, `bootstrap.min.js`, `owl.carousel.min.js` (and the rest) should be **200**, not 404.
   - No “Refused to apply style… MIME type ('text/html')” or “Refused to execute script… MIME type ('text/html')”.
   - No `$ is not defined` in the console.
4. **Home page** with the search/map: geocomplete and map should work; if our jQuery 404’d, the CDN fallback should still provide `$`.

## If 404s Persist

- **Build fails at verification**: `collectstatic` is not placing those paths under `STATIC_ROOT`. Check:
  - `STATICFILES_DIRS` includes `BASE_DIR/static` and that `static/css/`, `static/js/villareal/`, `static/css/img/`, `static/css/libraries/` exist in the repo.
  - `STATIC_ROOT` (e.g. `staticfiles`) is used consistently and not overwritten by `STATICFILES_STORAGE` in a way that skips these files.
- **Build passes, 404s in browser**:
  - Confirm WhiteNoise is in `MIDDLEWARE` for staging and not removed.
  - Confirm the service runs with the same `STATIC_ROOT` as in the build (no different `BASE_DIR` or cwd at runtime).
  - On Render, ensure the built filesystem (including `staticfiles/`) is what the running container uses (e.g. no extra “output” or “publish” dir that omits `staticfiles`).

## Reverting to CompressedStaticFilesStorage (Optional)

After 404s are resolved, you can try switching back to `CompressedStaticFilesStorage` in staging for smaller on-disk files and pre-compressed .gz:

1. In `staging.py`, set:
   - `STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'`
   - `STORAGES["staticfiles"]["BACKEND"] = 'whitenoise.storage.CompressedStaticFilesStorage'`
2. Redeploy and re-check build verification and browser Network/console. If 404s return, the issue is likely in `post_process` or the build image (e.g. brotli); keep `StaticFilesStorage` for staging.
