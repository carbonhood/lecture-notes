# Deploy this site to barrettlemons.com

This folder is a complete, static Netlify site for **https://barrettlemons.com**.

## What changed (audit implementation)

- Canonical, Open Graph, and schema URLs now use `https://barrettlemons.com/` (not the Netlify subdomain)
- `robots.txt` and `sitemap.xml` point at the custom domain
- `netlify.toml` + `_redirects` force `barrettlemons.netlify.app` → `barrettlemons.com`
- Public phone removed from Contact (phone remains on the résumé PDF for applications)
- About rewritten for recruiter skim order (ask → KUB proof → school → Spanish)
- Skills updated (PLS-CADD, field inspection, Python)
- SSTA caption clarifies team context vs personal credit
- GitHub + Little Pink scholarship essay linked in footer / `sameAs`
- Writing soft-launched with three posts (`writing/posts.json`)

## Deploy

1. In Netlify, connect this folder as the publish directory (or copy these files into your existing site repo and push).
2. Domain management → set **barrettlemons.com** as the primary domain.
3. Confirm `https://barrettlemons.netlify.app/` 301-redirects to `https://barrettlemons.com/`.
4. View page source on the live homepage and verify `rel="canonical"` is `https://barrettlemons.com/`.
5. Submit `https://barrettlemons.com/sitemap.xml` in Google Search Console and Bing Webmaster Tools (see `../online-presence/SEARCH_CONSOLE.md`).

## Local preview

```bash
cd website
python3 -m http.server 8080
# open http://127.0.0.1:8080
```
