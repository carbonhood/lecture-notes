# Online presence implementation pack

Implements the **Barrett Lemons — Professional Online Presence Audit** action plan.

## Contents

| Path | Purpose |
|------|---------|
| [`../website/`](../website/) | Deployable personal site (SEO fixes, privacy, Writing posts, résumé) |
| [`SEARCH_CONSOLE.md`](SEARCH_CONSOLE.md) | Google + Bing indexing steps (manual) |
| [`LINKEDIN_COPY_PACK.md`](LINKEDIN_COPY_PACK.md) | Headline, About, Featured, recommendation email, post drafts |
| [`GITHUB_CLEANUP.md`](GITHUB_CLEANUP.md) | Profile + repo hygiene (manual; API blocked here) |
| [`github-profile/`](github-profile/) | Profile README + pinned-repo README starters |
| [`HANDSHAKE_AND_EXPO.md`](HANDSHAKE_AND_EXPO.md) | Handshake + UTK Expo recruiting plan |
| [`EMAIL_AND_QUARTERLY_SYNC.md`](EMAIL_AND_QUARTERLY_SYNC.md) | Domain email + quarterly checklist |

## Done in code / files

- P0 SEO: canonical, OG, schema, robots, sitemap → `barrettlemons.com`
- P0 redirects: `netlify.toml` + `_redirects`
- P0 privacy: phone removed from public Contact
- P0 résumé: site URL + PLS-CADD on PDF
- P1 site links: GitHub + Little Pink in footer / `sameAs`
- P1–P2 Writing: three posts live in `website/writing/`

## Still requires you (accounts we cannot access)

1. Deploy `website/` to Netlify and set primary domain
2. Search Console + Bing sitemap submit
3. Paste LinkedIn copy pack
4. Apply GitHub profile/repo cleanup in the GitHub UI
5. Update Handshake + Expo registration

## Local preview

```bash
cd website && python3 -m http.server 8080
```
