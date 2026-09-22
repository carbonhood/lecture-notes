# Domain email + quarterly presence sync

## Domain email (optional, recommended)

DNS for `barrettlemons.com` already shows Spaceship nameservers / MX launch records. Personal branded mail is not required for Summer 2027, but it looks polished.

### Simple setup (forwarding)

1. In Spaceship (or your DNS host), create an email forward:
   - `hello@barrettlemons.com` → `bardlemons@gmail.com`
2. In Gmail → Settings → Accounts → **Send mail as** → add `hello@barrettlemons.com` (follow SPF/DKIM instructions Spaceship provides).
3. Update site Contact + LinkedIn About to list `hello@barrettlemons.com` once deliverability is confirmed.
4. Keep Gmail as the inbox; do not abandon `bardlemons@gmail.com` until you have tested replies for a week.

### Do not

- Publish a phone number on the website
- Use a joke / nickname address on applications

## Quarterly sync checklist

Run every January / April / July / October (15 minutes):

- [ ] Résumé PDF dates match LinkedIn and the homepage
- [ ] Homepage About still states the current internship target term
- [ ] New projects (SSTA, glider, coursework) have non-confidential photos + captions
- [ ] Writing: at least one new post **or** explicitly pause the blog (no empty promises)
- [ ] GitHub: only pin repos you’d show a utility recruiter
- [ ] Google yourself in an incognito window — note top 5 results
- [ ] Confirm `barrettlemons.netlify.app` still 301s to `barrettlemons.com`
- [ ] Confirm canonical tags still show the custom domain (View Source)

## Privacy reminders

| Surface | Phone | Email | Address |
|---------|-------|-------|---------|
| Website | No | Yes | City/state only in footer |
| Résumé PDF / Handshake | Yes | Yes | City/state (+ ZIP optional) |
| LinkedIn public | No | Via LinkedIn | Region only |
