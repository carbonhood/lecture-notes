# Search Console & Bing — index barrettlemons.com

Do this **after** deploying the fixed site (canonical URLs must already say `barrettlemons.com`).

## Google Search Console

1. Open [Google Search Console](https://search.google.com/search-console).
2. Add property → **URL prefix** → `https://barrettlemons.com`.
3. Verify ownership (easiest: HTML file upload to the site root, or DNS TXT at Spaceship).
4. Sitemaps → Add sitemap → `sitemap.xml` (full URL: `https://barrettlemons.com/sitemap.xml`).
5. URL Inspection → inspect `https://barrettlemons.com/` → **Request indexing**.
6. Also inspect each writing URL once they are live:
   - `https://barrettlemons.com/writing/`
   - `https://barrettlemons.com/writing/utility-pole-relocation.html`
   - `https://barrettlemons.com/writing/reading-the-spec-book.html`
   - `https://barrettlemons.com/writing/glider-trade-offs.html`
7. Optional cleanup: if Search Console ever shows `barrettlemons.netlify.app` as indexed, use Removals only after the 301 redirect is confirmed.

## Bing Webmaster Tools

1. Open [Bing Webmaster](https://www.bing.com/webmasters).
2. Add site `https://barrettlemons.com` (can import from Google Search Console).
3. Submit `https://barrettlemons.com/sitemap.xml`.
4. Use URL Submission for the homepage once.

## Success criteria (1–2 weeks)

- `site:barrettlemons.com` returns the homepage (and ideally Writing).
- Searching `Barrett Lemons` starts surfacing the personal site near Knox News / legislative results.
- No primary ranking for `barrettlemons.netlify.app`.
