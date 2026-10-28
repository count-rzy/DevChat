# DevChat task status

Checklist items are marked complete only where the current implementation has been inspected. This file is a verified snapshot, not a claim that planned features exist.

## Implemented

- [x] Django project and PostgreSQL configuration.
- [x] `GET /api/health/` database health endpoint.
- [x] `InviteCode` model and Django Admin management.
- [x] `POST /api/accounts/register/` with username/password validation, Django password hashing, CSRF protection, and transactional single-use invitation handling.
- [x] Development-only browser registration form that submits through the existing CSRF-protected API and is hidden when `DEBUG=False`.
- [x] Session authentication endpoints: CSRF bootstrap, login, logout, and current user.
- [x] CSRF-protected state-changing auth endpoints and HttpOnly session cookies.
- [x] Tests for registration, invitations, passwords, sessions, current-user permissions, CSRF, and concurrent invitation consumption.
- [x] Next.js App Router chat prototype using JavaScript and CSS Modules.
- [x] Frontend request to the backend health endpoint.
- [x] English and Russian translations for the current prototype UI.
- [x] Browser-language detection, English fallback, manual language selection, and local preference persistence.

## Incomplete or unverified

- [ ] Verify frontend localization behavior in both languages, unsupported-browser fallback, and saved preference after reload.
- [ ] Add production Next.js registration/login pages and connect them to the CSRF/session API (the Django registration page is development-only).
- [ ] Review the development registration page visually in a browser at desktop/mobile sizes and in English/Russian.
- [ ] Add authentication rate limiting and brute-force protection.
- [ ] Define and implement profile and avatar APIs, storage, upload validation, and owner-only permissions.
- [ ] Persist chat conversations and messages in PostgreSQL and enforce membership permissions.
- [ ] Localize future screens, backend-facing errors, and locale-sensitive date displays.
- [ ] Decide account/local language preference synchronization after profiles and authentication exist.
- [ ] Add realtime messaging and attachments only after persistent messaging is established.
- [ ] Configure production secrets, allowed hosts, deployment, and media storage.

## Current limitations

- Chat contacts and messages are sample data held in frontend React state; sending a message does not persist it.
- The language setting is stored in browser local storage and is not associated with an account.
- `DEBUG` defaults to true for local development. Production still needs a stable secret, allowed hosts, exact deployed CORS/CSRF origins, HTTPS, and a reviewed deployment configuration.
- No authentication rate limiting or brute-force protection is implemented.
- No end-to-end encryption is implemented or claimed.

## Verification record

- Repository audit and implementation inspection completed on 2026-10-28.
- `npm run lint` passed.
- `npm run build` passed with Next.js 16.4.3.
- `python manage.py test accounts.tests` passed 16 tests, including registration, authentication, CSRF, concurrent invite consumption, and DEBUG-only page rendering.
- `python manage.py check` passed with no issues.
- Migration checks (`makemigrations --check --dry-run` and `migrate --check`) passed on 2026-10-28.
- `git diff --check` passed; Git reported expected LF-to-CRLF conversion warnings.
- Manual browser checks for frontend language selection, fallback, reload persistence, and the registration page's visual layout remain pending; no frontend test runner is configured.
