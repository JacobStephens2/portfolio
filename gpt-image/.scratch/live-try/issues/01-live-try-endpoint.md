# 01 — Live try endpoint (subscribe + generate + log)

**What to build:** A visitor can POST a prompt, email, and Turnstile token and receive either a generated image (as base64) or a clear error. Success also adds them to the newsletter list and appends a metrics event.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Turnstile verified before any OpenAI call
- [ ] Newsletter list membership updated via admin API
- [ ] Rate limits enforced for IP and email
- [ ] Trial event appended on every attempt (success and handled failure)
- [ ] Response never leaks secrets
