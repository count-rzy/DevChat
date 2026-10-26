# DevChat — Agent Instructions

## Project rules

- Read `README.md` before substantial changes.
- Follow the existing architecture and work incrementally.
- Do not rewrite unrelated code or introduce unnecessary dependencies.
- Ask before making major architectural changes.

## Stack

- Frontend: Next.js App Router, React, JavaScript, CSS Modules.
- Backend: Python, Django, Django REST Framework, PostgreSQL.
- Do not introduce TypeScript or Tailwind CSS.
- Follow the additional instructions in `frontend/AGENTS.md` when working on the frontend.

## Security

- Never commit secrets, credentials, `.env` files, database dumps, or private user data.
- Read sensitive configuration from environment variables.
- Never expose private messages or protected API data to unauthorized users.
- Do not claim end-to-end encryption unless it is actually implemented.

## Quality and Git

- Inspect relevant files before editing.
- Run appropriate checks and tests after changes when possible.
- Report what changed and which checks were run.
- Preserve existing user changes.
- `main` is stable; use `dev` for integration.
- Never commit directly to `main` or run destructive Git commands without approval.