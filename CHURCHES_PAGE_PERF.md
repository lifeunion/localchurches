# /churches/ Page – Performance Notes

## Implemented (reduce 2.7–3.8s)

1. **ChurchIndexPage.church_posts() – `.only()`**
   - Selects only the fields used in the table: `id`, `slug`, locality and contact fields.
   - Cuts down DB work and memory.

2. **ChurchIndexPage.serve() – view-level cache**
   - Full HTML cached 10 min, key `church_index_html_{tag}`.
   - `Cache-Control: public, max-age=600` for browser caching.
   - Cache cleared on ChurchPage `post_save` / `post_delete` for `church_index_html_all` (tag-specific keys still expire by TTL).

3. **Template – avoid `branch.url`**
   - Replaced `{{ branch.url }}` with `/churches/{{ branch.slug }}/` to avoid per-row URL resolution.

4. **base_blog – preload main CSS**
   - `rel="preload"` for `villareal-turquoise.css` so the browser can start the request earlier.

## Already in place

- **/api-localities/**: `values()` queryset, 60 min response cache; used by mobile DataTables after load, so it doesn’t add to TTFB.

## Possible next steps (if still slow)

- **Server-side DataTables**: Move the desktop table to AJAX + server-side processing; paginate in the DB (e.g. 50 per page) instead of rendering all rows in HTML.
- **DB index**: `(path, live)` (or equivalent) if the churches query is still heavy; Wagtail may already add this.
- **Fragment cache**: `{% cache 600 church_index_tbody request.GET.tag %}…{% endcache %}` around the table body if view cache is not used.
- **Assets**: Defer DataTables (and possibly jQuery) and move the init into a deferred script to reduce parser blocking; needs testing.
- **CDN**: Ensure `villareal-turquoise.css` and main JS are behind a CDN with long `max-age` and compression (Brotli/gzip).

## How to verify

- Before/after: time `curl -w '%{time_total}\n' -o /dev/null -s 'https://localchurches.onrender.com/churches/'`.
- Second load (cache hit): should be much faster.
- After editing a church: first request can be a cache miss; next request within 10 min should be fast.
