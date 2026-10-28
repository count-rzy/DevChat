# DevChat

**DevChat** is a private messaging web application for a small, invite-only group of users. The project is developed as a full-stack application and a GitHub portfolio project.

**DevChat** — приватный веб-мессенджер для небольшой группы пользователей с регистрацией по приглашениям. Проект разрабатывается с нуля для личного использования и в качестве full-stack проекта в GitHub-портфолио.

> **Project status:** The Django foundation, single-use invite registration, and session-based authentication API are implemented. The Next.js frontend remains a local-state chat prototype with English and Russian UI translation. Persistent messages, user profiles, and avatar management are not implemented.

> **Development wave status:** Wave 1 (project foundation, backend health endpoint, and chat prototype) is complete. Wave 2 (invite-only registration and Django session authentication with CSRF) is implemented and covered by tests; authentication abuse protection remains planned.

> Статус волн: волна 1 (основа проекта, endpoint проверки доступности бэкенда и прототип чата) завершена. Волна 2 (регистрация по приглашениям и session-авторизация с CSRF) реализована и проверена тестами; защита от злоупотреблений входа ещё не реализована.

> **Статус проекта:** реализованы основа Django, регистрация с одноразовыми пригласительными кодами и API сессионной авторизации. Frontend на Next.js остаётся прототипом переписки с локальным состоянием и переводом интерфейса на английский и русский. Сохранение сообщений, профили и управление аватарками пока не реализованы.

## 1. Project goals / Цели проекта

- Private messaging for a limited group of invited users.
- Direct conversations between users.
- Secure account registration and authentication.
- Editable user profiles and avatars.
- English and Russian interface.
- Responsive interface for desktop and mobile devices.
- Real-time messaging after the core messaging functionality is stable.

- Приватная переписка для ограниченного круга приглашённых пользователей.
- Личные диалоги между пользователями.
- Безопасная регистрация и авторизация.
- Редактируемые профили и аватарки.
- Интерфейс на русском и английском языках.
- Адаптивная работа на компьютерах и мобильных устройствах.
- Обмен сообщениями в реальном времени после стабилизации основной функциональности.

The application is not intended to be a public social network. Features should be implemented only when they serve the project's actual requirements.

Приложение не предназначено для создания публичной социальной сети. Дополнительные функции следует добавлять только при наличии конкретной необходимости.

## 2. Technology stack / Технологический стек

| Layer | Technology |
|---|---|
| Frontend | Next.js 16.4.3, React 19.3.0, JavaScript |
| Styling | CSS Modules, global CSS |
| Backend | Python, Django 5.2.18, Django REST Framework 3.18.3 |
| Database | PostgreSQL 18 |
| Realtime | Django Channels, WebSockets — planned |
| Realtime infrastructure | Redis — only if needed |
| Version control | Git, GitHub |

TypeScript and Tailwind CSS are not part of the current project requirements. Do not introduce them without explicit approval.

TypeScript и Tailwind CSS не входят в текущие требования. Не добавлять их без отдельного согласования.

## 3. Repository structure / Структура проекта

```text
DevChat/
├── backend/
│   ├── .venv/                 # Local Python environment; not committed
│   ├── config/                # Django project configuration
│   ├── core/                  # Health endpoint and core utilities
│   ├── accounts/              # Accounts and invitation codes
│   │   └── templates/accounts/ # Development-only registration page
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example           # Environment variable template
├── frontend/
│   ├── app/
│   │   ├── lib/               # API utilities and translations
│   │   ├── page.js
│   │   ├── page.module.css
│   │   └── globals.css
│   ├── public/
│   └── package.json
├── README.md
├── TASK.md
└── .gitignore
```

This is the current logical structure, not a guarantee that every future file already exists. Update it when the verified project structure changes.

Это логическая структура проекта. Она не означает, что все перечисленные будущие файлы уже существуют. Обновляйте её по мере реальных изменений.

## 4. Architecture / Архитектура

### Frontend

The frontend is responsible for pages, components, user interactions, visual themes, language selection, and communication with the backend API.

Frontend отвечает за страницы, компоненты, взаимодействие с пользователем, оформление, выбор языка и обращения к backend API.

### Backend

The backend is the source of truth for authentication, permissions, validation, business logic, and access to user data. Django REST Framework is installed; account endpoints currently use Django JSON views and DRF serializers for request validation.

Бэкенд является источником истины для авторизации, прав доступа, проверки данных, бизнес-логики и доступа к данным. Django REST Framework установлён; endpoints аккаунтов сейчас реализованы как Django JSON views с DRF serializers для проверки запросов.

Backend является источником истины для авторизации, прав доступа, проверки входных данных, бизнес-логики и доступа к пользовательским данным.

### Database

The current database stores Django users and invitation-code records. Persistent profiles, conversations, and messages are planned and are not implemented yet.

Сейчас в базе хранятся пользователи Django и записи пригласительных кодов. Постоянные профили, диалоги и сообщения пока не реализованы и остаются в планах.

PostgreSQL хранит структурированные данные: пользователей, профили, пригласительные коды, диалоги, сообщения и другие записи по мере реализации функций.

### Media files

User-uploaded avatars and attachments should be stored as files, not as Git repository contents.

For local development, Django media storage may use a local `media/` directory. The database should store file references and related metadata rather than image binaries. Production storage can be selected later without coupling profile logic to a particular provider.

Пользовательские аватарки и вложения должны храниться как файлы, а не в репозитории Git.

В локальной разработке Django может использовать каталог `media/`. В базе данных следует хранить ссылки на файлы и необходимые метаданные, а не сами изображения в бинарном виде. Production-хранилище можно выбрать позднее.

### Environment variables

- Keep local secrets in `backend/.env`.
- Use `backend/.env.example` to document required variables without real credentials.
- Set a stable random `DJANGO_SECRET_KEY` in `backend/.env`; local development generates a temporary key when it is absent. Production startup requires `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=False`.
- Set `DJANGO_ALLOWED_HOSTS` and exact deployed frontend origins in `CSRF_TRUSTED_ORIGINS` for deployment.
- Never commit passwords, tokens, production credentials, or local databases.
- Frontend configuration should use environment variables such as `NEXT_PUBLIC_API_URL` where appropriate.
- Public frontend variables must never contain secrets.

## 5. Internationalization / Языковая система

DevChat must support **English and Russian** from the beginning of interface development.

DevChat должен поддерживать **английский и русский языки** с самого начала разработки интерфейса.

### Requirements

- Current frontend UI strings are held in `frontend/app/lib/translations.js` and selected with the language control in the profile footer.
- Support `en` and `ru` locale identifiers.
- Detect the browser's preferred supported language on first visit.
- Use English as the fallback when the browser language is unsupported.
- Allow the user to change the interface language manually.
- Persist the selected language across visits.
- Once profiles are implemented, associate the language preference with the authenticated user's profile and define how it synchronizes with the local preference.
- Do not translate user-generated messages automatically.
- Dates, times, and other locale-sensitive values should use appropriate locale formatting.
- Do not duplicate entire pages just to support another language.
- Do not hardcode new user-facing strings directly into components when they belong in translations.

### Требования

- Все надписи интерфейса должны проходить через единую систему локализации.
- Использовать идентификаторы языков `en` и `ru`.
- При первом посещении определять поддерживаемый язык браузера.
- Если язык не поддерживается, использовать английский.
- Предоставить ручное переключение языка.
- Сохранять выбранный язык между посещениями.
- После реализации профилей связать языковую настройку с аккаунтом и определить правила синхронизации с локальными настройками.
- Не переводить пользовательские сообщения автоматически.
- Форматировать даты и время с учётом выбранной локали.
- Не создавать отдельные копии страниц для каждого языка.
- Не размещать новые пользовательские надписи напрямую в компонентах, если они должны находиться в переводах.

The current implementation uses a small in-repository dictionary and React state; it does not add a localization dependency. Browser preferences are read client-side, while the server and hydration snapshots both use English to avoid mismatched initial markup. Only an explicit selector change writes the saved preference. User-authored sample messages are left as entered. The account preference synchronization policy remains open until authenticated profiles exist.

Текущая реализация использует небольшой словарь в репозитории и состояние React без дополнительной библиотеки. Настройки браузера читаются на клиенте, а серверный и гидратационный снимки используют английский язык, чтобы избежать расхождений начальной разметки. Сохранённое значение записывается только при явном переключении в селекторе. Примеры пользовательских сообщений остаются без изменений. Синхронизацию настройки с аккаунтом нужно определить после появления авторизованных профилей.

## 6. Accounts and profiles / Аккаунты и профили

### Registration

Registration is invite-only. An invitation code must be valid and unused. Each code may be used for one successful registration only.

Регистрация доступна только по приглашению. Код должен быть действительным и неиспользованным. Каждый код можно использовать только для одной успешной регистрации.

The current registration endpoint is:

`POST /api/accounts/register/`

Expected input:

```json
{
  "username": "example_user",
  "password": "a-strong-password",
  "invite_code": "valid-invitation-code"
}
```

The endpoint validates the username and applies Django's configured password validators. It creates the user through Django password hashing and marks the invitation as used in one transaction. The invitation row is locked during consumption, so concurrent registration attempts cannot both use the same code on databases that support row locking.

### Session authentication API

The backend uses Django sessions with `SessionAuthentication`; it does not issue JWTs or store long-lived tokens in the frontend. Session cookies are HttpOnly and SameSite Lax. Secure cookies are enabled when `DJANGO_DEBUG=False`.

| Method and endpoint | Purpose | Success response |
|---|---|---|
| `GET /api/accounts/csrf/` | Set the CSRF cookie and return a token | `{"csrfToken":"..."}` |
| `POST /api/accounts/register/` | Register with an invite | `201` with `message` and public `user` fields |
| `POST /api/accounts/login/` | Authenticate and create a session | `{"user":{"id":1,"username":"example_user"}}` |
| `POST /api/accounts/logout/` | End the authenticated session | `{"detail":"Logged out."}` |
| `GET /api/accounts/me/` | Return the current authenticated user | `{"user":{"id":1,"username":"example_user"}}` |

Registration request:

```json
{
  "username": "example_user",
  "password": "a-strong-password",
  "invite_code": "valid-invitation-code"
}
```

Login request:

```json
{
  "username": "example_user",
  "password": "a-strong-password"
}
```

Before every state-changing request, including registration and login, the client must call `GET /api/accounts/csrf/`, include browser credentials on the request, and send the returned token in the `X-CSRFToken` header. Django also sets the CSRF cookie. Login rotates the CSRF token, so fetch a fresh token after login before the next state-changing request. Invalid credentials return `401`; malformed or invalid registration/login data returns `400`; CSRF failures return `403`. The current-user endpoint returns `401` to anonymous users. Passwords and invite codes are never included in success responses.

The local frontend and API use different ports. For cookie-based requests, use a consistent host name on both sides (for example, `localhost`) and send `credentials: "include"`. Local frontend origins are explicitly listed in CORS and CSRF settings. For a deployed cross-origin frontend, configure its exact origin in `CSRF_TRUSTED_ORIGINS` and `CORS_ALLOWED_ORIGINS`; do not use wildcard origins.

Invitations are created through Django Admin or development tooling. There is no public invitation-generation endpoint.

API сессий использует стандартную авторизацию Django. Перед каждым изменяющим запросом клиент получает CSRF-токен, сохраняет cookie и отправляет токен в заголовке `X-CSRFToken` вместе с cookie сессии. При входе CSRF-токен обновляется. Endpoint текущего пользователя возвращает `401` для анонимных запросов. Публичного API для создания приглашений нет.

### Profiles

Planned profile fields include:

- Username.
- Display name.
- Avatar.
- Optional user description or status.
- Preferred interface language.
- Registration date.

The final model should be determined before implementation. Do not duplicate Django's user identity fields unnecessarily.

### Avatar management

- Validate actual file type and file size on the backend.
- Generate safe file names.
- Allow the owner to upload, replace, or remove their avatar.
- Use a default avatar when no custom avatar is present.
- Remove obsolete files safely when replacing or deleting an avatar, accounting for shared references if they are ever introduced.
- Never allow a user to modify another user's profile or avatar.
- Keep uploaded files and local media out of Git.
- Define upload restrictions and failure handling before enabling uploads.

## 7. Messaging / Переписка

Planned messaging features:

1. Private one-to-one conversations.
2. Conversation list and message history.
3. Sending and retrieving text messages through the API.
4. Editing and deleting messages with permission checks.
5. Replies and reactions.
6. Real-time message delivery through WebSockets.
7. Typing indicators and delivery/read statuses.
8. Attachments with strict file type and size restrictions.

The frontend currently contains a local-state chat prototype. Its sample messages are not persistent and must not be represented as real backend-backed conversations.

Текущий интерфейс содержит прототип переписки с данными в React state. Эти сообщения не сохраняются в базе и не должны описываться как полноценные диалоги.

Every conversation and message request must be authorized on the backend. Hiding a button in the frontend is not sufficient access control.

Каждый запрос к диалогу и сообщению должен проверяться на backend. Скрытие кнопки на frontend не заменяет проверку прав доступа.

## 8. Security principles / Принципы безопасности

- The backend enforces identity and access permissions.
- Use Django's password hashing and authentication facilities.
- Validate and normalize input on the backend.
- Apply appropriate CSRF, CORS, session/token, and request security controls.
- Do not allow arbitrary CORS origins in production.
- Keep secrets out of source code, documentation, frontend bundles, and Git history.
- Restrict uploads by actual content type and size.
- Prevent unauthorized access to conversations, messages, profiles, and media.
- Add appropriate throttling and brute-force protections before public deployment.
- Use HTTPS in production.
- Do not claim end-to-end encryption (E2EE): it is not currently part of the requirements.
- Do not disable security controls to make development easier.

## 9. Development workflow / Процесс разработки

### Git branches

- `main` is the stable branch.
- `dev` is the integration branch.
- Implement work on a dedicated task branch created from the latest `dev`.
- Use descriptive branch names, for example `feature/profile-management` or `feature/i18n`.
- Submit completed work through a Pull Request targeting `dev`.
- Do not merge development work into `main unless explicitly approved by the project owner.
- Do not rewrite shared history or force-push without explicit approval.
- `AGENTS.md` is a development instruction file and must not be merged into `main`.
- The developer may keep agent-specific instructions on `dev`; do not delete or untrack them merely to prepare a future merge.

### Codex rules

- Inspect the current repository, README, task list, relevant source files, and applicable local instructions before making changes.
- Work only on the requested scope.
- Preserve unrelated user changes.
- Avoid unnecessary dependencies and architecture rewrites.
- Run appropriate checks and tests.
- Update README and `TASK.md` after completing a task.
- Mark checklist items complete only when implementation and required verification have succeeded.
- Report failed checks, unimplemented requirements, and known limitations honestly.
- Never create commits, push, merge, or publish changes. Git operations that change repository history or remote state remain the developer's responsibility.
- Do not merge `AGENTS.md` into `main`.

## 10. Local setup / Локальный запуск

### Requirements

- Python and Node.js compatible with the installed project dependencies.
- PostgreSQL 18.
- Git.

### Backend

From the repository root in PowerShell:

```powershell
.\backend\.venv\Scripts\Activate.ps1
python backend\manage.py runserver
```

If the virtual environment does not exist yet, create it and install dependencies first:

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Create `backend/.env` from `backend/.env.example` and configure local database credentials before running migrations or starting Django.

```powershell
Copy-Item backend\.env.example backend\.env
python backend\manage.py migrate
python backend\manage.py check
```

Do not overwrite an existing `.env` without reviewing it first.

Health endpoint:

`http://127.0.0.1:8000/api/health/`

Expected successful response:

```json
{
  "status": "ok",
  "database": "connected"
}
```

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

If `node_modules` and dependencies are already installed, `npm install` is not required every time.

### PostgreSQL service on Windows

The local service may be checked with:

```powershell
Get-Service postgresql-x64-18
```

Start it from an elevated PowerShell if it is stopped:

```powershell
Start-Service postgresql-x64-18
```

### Local API configuration

The frontend currently defaults to:

`http://127.0.0.1:8000/api`

For session cookies during local development, the frontend and backend should use the same host name. To use `localhost`, set `NEXT_PUBLIC_API_URL=http://localhost:8000/api` in `frontend/.env.local`. Use `credentials: "include"` for browser API requests. Keep local settings out of committed secret files.

## 11. API status / Статус API

| Endpoint | Purpose | Status |
|---|---|---|
| `GET /api/health/` | Backend and database health check | Implemented |
| `GET /api/accounts/csrf/` | CSRF bootstrap for browser clients | Implemented |
| `POST /api/accounts/register/` | Invite-only registration | Implemented |
| `POST /api/accounts/login/` | Authenticate and start a Django session | Implemented |
| `POST /api/accounts/logout/` | End the current Django session | Implemented |
| `GET /api/accounts/me/` | Return the current authenticated user | Implemented |
| `GET /api/accounts/dev/register/` | Local browser registration test form; available only with `DEBUG=True` | Development only |
| Profile endpoints | Read and update profiles | Planned |
| Avatar endpoints | Upload, replace, and remove avatars | Planned |
| Conversation endpoints | Create and retrieve conversations | Planned |
| Message endpoints | Send and manage messages | Planned |

Endpoint status must reflect verified code, not the intended roadmap.

For local registration testing, open `http://127.0.0.1:8000/api/accounts/dev/register/` while Django runs with `DEBUG=True`. Create an invitation in Django Admin first. The form calls the same CSRF-protected registration API as other clients and is unavailable when `DEBUG=False`; it is not the production registration page.

Для локальной проверки регистрации откройте `http://127.0.0.1:8000/api/accounts/dev/register/`, когда Django запущен с `DEBUG=True`. Сначала создайте приглашение в Django Admin. Форма использует тот же API регистрации с защитой CSRF и недоступна при `DEBUG=False`; это не production-страница регистрации.



## 12. Roadmap / План разработки

The order can change when a dependency requires it, but each stage should have clear acceptance criteria.

Порядок может меняться при наличии технических зависимостей, но у каждого этапа должны быть понятные критерии завершения.

### Stage 1 — Foundation

- [x] Establish separate frontend and backend projects.
- [x] Configure Django and PostgreSQL connection.
- [x] Add the backend health endpoint.
- [x] Initialize the Next.js frontend using JavaScript and CSS Modules.
- [x] Connect the frontend to the health endpoint.
- [x] Prepare local environment configuration and basic project documentation.

### Stage 2 — Accounts and authentication

- [x] Add the `InviteCode` model.
- [x] Add invitation management through Django Admin.
- [x] Implement invite-only registration.
- [x] Hash passwords through Django's built-in user creation.
- [x] Prevent reuse of an invitation code.
- [x] Implement login and logout.
- [x] Choose and implement Django session authentication with CSRF protection.
- [x] Add tests for registration, invalid and reused invitations, duplicate usernames, password validation, authentication, and CSRF.
- [x] Add a PostgreSQL concurrency test for single-use invitation consumption.
- [x] Add a `DEBUG=True` browser registration form that uses the existing CSRF-protected API.
- [ ] Add appropriate abuse protection for authentication endpoints.

### Stage 3 — Profiles and localization

- [ ] Define the user profile model and API.
- [ ] Implement profile read/update permissions.
- [ ] Implement safe avatar upload, replacement, and deletion.
- [x] Add English and Russian translations for the current prototype interface.
- [x] Implement browser language detection, manual selection, and local persistence for the prototype.
- [ ] Synchronize language preference with the user profile after authentication is available.
- [ ] Test localization fallback and profile access controls.

### Stage 4 — Private messaging

- [ ] Define conversation and message models.
- [ ] Implement private one-to-one conversations.
- [ ] Implement message history and sending through the API.
- [ ] Enforce conversation membership on every relevant request.
- [ ] Add tests for messaging and access restrictions.

### Stage 5 — Frontend integration

- [ ] Replace sample chat data with backend data.
- [ ] Add production Next.js registration and login screens; the existing Django registration form is development-only.
- [ ] Add profile settings and avatar controls.
- [ ] Add conversation list and message history.
- [ ] Add light and dark themes.
- [ ] Verify responsive layouts and both interface languages.

### Stage 6 — Realtime and attachments

- [ ] Integrate Django Channels and WebSockets.
- [ ] Add real-time message delivery.
- [ ] Add typing indicators.
- [ ] Add delivery and read statuses.
- [ ] Add attachment upload with file restrictions.
- [ ] Introduce Redis only if required by the chosen deployment architecture.

### Stage 7 — Testing and deployment

- [ ] Expand backend and frontend automated tests.
- [ ] Review authentication, authorization, uploads, and request limits.
- [ ] Verify configuration and secret handling for production.
- [ ] Choose hosting and media storage.
- [ ] Document production deployment.
- [ ] Verify the application in a clean environment.

## 13. Current limitations / Текущие ограничения

- Chat messages are currently prototype data held in frontend state.
- Production Next.js registration and login screens are not implemented. A separate Django registration test form is available only with `DEBUG=True`.
- Authentication endpoints do not yet have rate limiting or brute-force protection.
- User profile management and avatar uploads are planned.
- Localization currently covers the prototype's interface labels; dates, fixture previews, backend responses, and future screens are not fully localized.
- The frontend uses local storage for language preference until an authenticated profile preference exists.
- Local development defaults to `DEBUG=True`; production must set `DJANGO_DEBUG=False`, a secret `DJANGO_SECRET_KEY`, allowed hosts, exact CORS/CSRF frontend origins, and HTTPS.
- Real-time messaging and attachments are planned.
- End-to-end encryption is not implemented or promised.
- Production hosting and storage have not yet been selected.

## 14. License

No license has been selected yet. Do not assume that the project is open-source or add a license without the owner's decision.
