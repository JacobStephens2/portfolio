# Spec: Live try gpt-image (newsletter-gated)

## Problem Statement

Visitors to the gpt-image landing page can only read about the CLI. They cannot try a prompt in-browser, and Jacob cannot see how many people attempted a trial or subscribed through that path.

## Solution

A CLI-shaped try panel on the landing page. The visitor types a prompt as if running `gpt_image.py generate`. Submitting requires an email newsletter signup protected by Cloudflare Turnstile. On success the page shows a generated image, the visitor is added to the stephens newsletter list, and dashboard.stephens.page shows usage metrics.

## User Stories

1. As a visitor, I want a terminal-like prompt box, so that I understand this is a CLI tool.
2. As a visitor, I want to type an image description and press Enter/Generate, so that I can try the product.
3. As a visitor, I want to be asked for email + Turnstile before generation, so that the free trial is gated fairly.
4. As a visitor, I want a clear message that I'm joining Jacob's newsletter, so that I consent knowingly.
5. As a visitor, I want an image back when generation succeeds, so that the trial feels real.
6. As a visitor, I want friendly errors (rate limit, bad email, Turnstile fail, API down), so that I know what to do next.
7. As a visitor already subscribed, I want generation to still work, so that I'm not blocked.
8. As a bot, I want to be blocked by Turnstile and honeypot, so that I don't burn API spend.
9. As Jacob, I want dashboard metrics for trials (counts, recent prompts/emails, success rate), so that I can measure interest.
10. As Jacob, I want newsletter membership updated via the existing service, so that I don't run a second list.
11. As Jacob, I want hard rate limits per IP and email, so that OpenAI cost stays bounded.
12. As a keyboard user, I want the try panel operable without a mouse.
13. As a visitor with JS disabled, I may not run the interactive try, but the static page still documents the CLI.
14. As Jacob, I want secrets only in private env files, so that keys never ship in the public repo.

## Implementation Decisions

### Modules

1. **LiveTry (public seam)** - one HTTP POST interface:
   - In: prompt, email, cf-turnstile-response, honeypot
   - Out: JSON `{ok, message, image_b64?, already_subscribed?}`
   - Implementation: PHP handler on stephens.page (same pattern as contact form): Turnstile verify → rate limit → newsletter admin add (list `stephens`) → OpenAI images.generate (model gpt-image-2, quality medium, size 1024x1024) → append trial event → return b64 PNG.

2. **TrialLog** - append-only JSONL of events for metrics (path fixed under `/var/lib/gpt-image/`).

3. **Dashboard gpt-image panel** - authenticated partial reading TrialLog: totals, unique emails, success/fail, last N events (prompt truncated, email shown).

4. **Landing page UI** - CLI term, prompt input, gate panel (email + Turnstile + consent copy), result image area.

### Seams for testing

Primary external seam: **LiveTry POST** (behavior tests via request/response with faked Turnstile/OpenAI in unit tests later; smoke with real keys carefully).

Dashboard seam: **TrialLog read** (parse JSONL → stats object).

### Rate limits

- 3 successful generations per email per 24h
- 5 attempts per IP per hour
- Prompt max 500 characters

### Newsletter

- After Turnstile success, call newsletter admin `POST /admin/add` with the email (confirmed). Message in UI: joining Jacob Stephens' blog newsletter; unsubscribe links in every email.

## Testing Decisions

- Prefer behavior at LiveTry: invalid email → error; empty turnstile → error; honeypot filled → fake success without spend.
- Dashboard: empty log → zeros; N events → correct counts.
- Manual smoke: one real generate with Resend sim / personal email if needed.

## Out of Scope

- Multi-image batch from the browser
- Edit path in the browser
- Emailing the image to the user
- Double opt-in for this path (admin-add is immediate confirm; public blog subscribe stays double opt-in)
- Charging users or accounts beyond newsletter gate
- Mobile native apps

## Further Notes

Turnstile site key is already public on the contact form path. Reuse the same site key/secret from `private/.env`.
