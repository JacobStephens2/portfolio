# Research: gpt-image live try (newsletter-gated)

## Question

How should a browser “try gpt-image” flow subscribe users, call image generation, and report usage on dashboard.stephens.page, reusing existing fleet seams?

## Primary sources (this host)

### stephens.page contact form (PHP + Turnstile)

- `contact-submit.php` loads secrets from `private/.env`, verifies Cloudflare Turnstile via `siteverify`, honeypot `website_url`, IP rate limit in temp files, Resend send, JSON responses.
- Pattern to copy for public POST handlers on the static site.

### Newsletter service (Rust/Axum)

- Public: `POST /subscribe` with form fields `email`, `cf-turnstile-response`, `list`, honeypot `website_url`. Double opt-in; rate limit 5/hour/IP.
- Turnstile is one-time: a token cannot be verified by both the landing page backend and newsletter subscribe.
- Admin (bearer `NEWSLETTER_ADMIN_TOKEN`): `POST /admin/add` adds email as **confirmed** on a list (`stephens` default). Used by the dashboard already.
- CORS allows `https://stephens.page`.
- Listens on `127.0.0.1:3462` (dashboard default `NEWSLETTER_ADMIN_URL`).

### Dashboard (FastAPI)

- Auth-gated UI; newsletter tab proxies admin API (`app/newsletter.py`).
- Signups tab aggregates per-app adapters via `recent_signups`.
- Config via `/var/www/dashboard.stephens.page/.env`.
- Partials under `app/templates/partials/`; tabs in `dashboard.html`.

### gpt-image CLI

- OpenAI Images API via `client.images.generate` (`gpt-image-2`, quality, size, b64_json).
- Expensive at high/1536; free public trial should use medium/1024.

## Decisions grounded in sources

1. **One deep public module**: a single POST endpoint on stephens.page that owns Turnstile → subscribe → generate → metrics write. Callers only know “prompt + email + turnstile token in, image or error out.”
2. **Subscribe after our Turnstile verify** via newsletter **admin add** (confirmed), because the public subscribe endpoint would re-consume the Turnstile token. Document that live-try confirms immediately (unsubscribe still works).
3. **Metrics**: append-only JSONL under `/var/lib/gpt-image/trials.jsonl` readable by dashboard (same box). Avoid giving dashboard a second write path into newsletter SQLite.
4. **Rate limits**: IP + email caps in the PHP module to protect OpenAI spend.
5. **UI**: CLI-shaped terminal on `/gpt-image/`; submit opens gate (email + Turnstile); success paints image like the hero frame.
