# DevChat

**DevChat** is a private messaging web application for a small, invite-only group of users. The project is developed as a full-stack application and a GitHub portfolio project.

**DevChat** — приватный веб-мессенджер для небольшой группы пользователей с регистрацией по приглашениям. Проект разрабатывается с нуля для личного использования и в качестве full-stack проекта в GitHub-портфолио.

> **Project status:** Django invite registration, session authentication, temporary auth request limits, user profiles, private one-to-one conversations, and persistent text messages are implemented. The Next.js frontend includes English/Russian authentication, profile editing, conversation lists, and message history/sending connected to the backend. Avatar upload, realtime delivery, attachments, and manual browser verification remain incomplete.

> **Development wave status:** The foundation and account/authentication work is complete, including session auth with CSRF and temporary request limits. Profiles, private persistent text messaging, and frontend API integration are implemented. Realtime, avatar uploads, attachments, and production cache/proxy configuration remain future work.

> Статус разработки: основа и аккаунты с авторизацией завершены, включая session-auth с CSRF и временные лимиты запросов. Профили, приватные сохраняемые текстовые сообщения и интеграция frontend с API реализованы. Realtime, загрузка аватаров, вложения, production-cache и настройка proxy остаются будущими задачами.

> **Статус проекта:** реализованы регистрация по приглашениям, сессионная авторизация, временные лимиты auth-запросов, профили, приватные диалоги один на один и сохранение текстовых сообщений. Frontend на Next.js поддерживает вход и регистрацию, редактирование профиля, список диалогов и историю/отправку сообщений на английском и русском языках. Загрузка аватаров, realtime-доставка, вложения и ручная проверка в браузере пока не завершены.

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

The database stores Django users and invitation codes, one profile per user, private one-to-one conversations, and text messages. The profile migration creates a profile row for every existing user with empty display name/description and English as the default preference; it does not rewrite user or invitation rows. The messaging migration creates new tables and indexes only. Reversing the profile migration drops its new profile table and profile data, while leaving user and invitation tables intact. Review the manual verification steps below before applying migrations to an existing local database.

В базе хранятся пользователи Django и приглашения, отдельный профиль пользователя, приватные диалоги один на один и текстовые сообщения. Миграция профилей создаёт строки профиля существующим пользователям с пустыми отображаемым именем и описанием и языком `en` по умолчанию; она не меняет строки пользователей и приглашений. Миграция переписки добавляет только новые таблицы и индексы. Откат миграции профиля удалит новую таблицу профилей и её данные, но не таблицы пользователей и приглашений.

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

The current implementation uses a small in-repository dictionary and React state; it does not add a localization dependency. Browser preferences are read client-side, while the server and hydration snapshots both use English to avoid mismatched initial markup. Before sign-in, the explicit language selector persists the preference locally; after sign-in, the profile preference is synchronized with the interface. User-authored messages are left as entered.

Текущая реализация использует небольшой словарь в репозитории и состояние React без дополнительной библиотеки. Настройки браузера читаются на клиенте, а серверный и гидратационный снимки используют английский язык, чтобы избежать расхождений начальной разметки. Сохранённое значение записывается только при явном переключении в селекторе. Примеры пользовательских сообщений остаются без изменений. Синхронизацию настройки с аккаунтом нужно определить после появления авторизованных профилей.

## 6. Accounts and profiles / Аккаунты и профили

The Next.js frontend provides `/login` and `/register`. Registration requires a one-time invitation and creates the account without automatically starting a session; the user then signs in. Authenticated sessions are restored through `/api/accounts/me/`, and the chat redirects anonymous users to sign-in. The session cookie remains HttpOnly; no password or auth token is stored in browser local storage.

Authenticated users can read and update their own display name, description, and preferred language using `GET /api/accounts/profile/` and `PATCH /api/accounts/profile/update/`. `GET /api/accounts/users/` lists active users and `GET /api/accounts/users/<id>/` returns public profile details. Avatar upload is not implemented.

Пользователь после входа может читать и менять собственное отображаемое имя, описание и язык через `GET /api/accounts/profile/` и `PATCH /api/accounts/profile/update/`. `GET /api/accounts/users/` возвращает список активных пользователей, а `GET /api/accounts/users/<id>/` — публичные данные профиля. Загрузка аватаров не реализована.

Authentication endpoints apply fixed-window request limits: login allows 10 attempts per minute for an IP and username pair and 30 attempts per minute per IP; registration allows 5 attempts per hour per IP. Excess requests receive `429` and `Retry-After`. The default Django cache is process-local, so production deployments with multiple workers must configure a shared cache backend. Limits use `REMOTE_ADDR`; behind a reverse proxy this may be the proxy address for every visitor and cause them to share one limit. Configure trusted client-address handling at the deployment boundary before exposing the service. Forwarded headers are not trusted by this code.

Фронтенд Next.js предоставляет страницы `/login` и `/register`. Для регистрации нужен одноразовый код приглашения; после создания аккаунта пользователь входит отдельно. Сессия восстанавливается через `/api/accounts/me/`, а неавторизованный пользователь перенаправляется со страницы прототипа чата на вход. Cookie сессии остаётся HttpOnly; пароль и токен авторизации не сохраняются в localStorage.

Для auth endpoint-ов действуют ограничения на фиксированное окно: до 10 попыток входа в минуту для сочетания IP и имени пользователя, до 30 попыток в минуту с одного IP и до 5 попыток регистрации в час с одного IP. Превышение возвращает `429` и `Retry-After`. Стандартный cache Django хранит данные в памяти процесса, поэтому production с несколькими workers требует общего cache backend. Лимиты используют `REMOTE_ADDR`; за reverse proxy это может быть адрес прокси для всех посетителей, и тогда лимит будет общим. До публикации сервиса настройте безопасное определение адреса клиента на границе инфраструктуры. Заголовки `X-Forwarded-*` код не считает доверенными.

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

Login and registration requests are rate limited using Django's cache: 10 login attempts per minute for an IP/username pair, 30 per minute for an IP, and 5 registrations per hour for an IP. Limits are fixed-window counters and return `429` with `Retry-After`. The default cache is in-process and is suitable only for single-process development; multi-worker deployments need a shared cache. Behind a reverse proxy, `REMOTE_ADDR` may identify the proxy for all clients, so the current limits can throttle them together. Configure trusted client-address handling at the deployment boundary before exposing the service; this application does not trust forwarded headers.

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

The frontend uses backend-backed private conversations and persistent text messages. Messaging uses HTTP; realtime delivery, attachments, editing, and deletion are not implemented.

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

The frontend uses `NEXT_PUBLIC_API_URL` when set. Otherwise, it targets port `8000` on the hostname used to open the frontend, so `localhost:3000` pairs with `localhost:8000` and `127.0.0.1:3000` pairs with `127.0.0.1:8000`. Set `NEXT_PUBLIC_API_URL=http://localhost:8000/api` in `frontend/.env.local` when you want to choose the backend host explicitly. Browser API requests use `credentials: "include"`. Keep local settings out of committed secret files.

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
| `POST /api/accounts/login/` and `POST /api/accounts/register/` | Fixed-window request limits; see account security notes | Implemented |
| `GET /api/accounts/profile/` and `PATCH /api/accounts/profile/update/` | Read/update current user profile and language | Implemented |
| Avatar endpoints | Upload, replace, and remove avatars | Planned |
| `GET /api/messaging/` and `POST /api/messaging/` | List or create private one-to-one conversations | Implemented |
| `GET /api/messaging/<id>/messages/` and `POST /api/messaging/<id>/messages/` | Retrieve/send text messages (members only; GET supports `before=<message_id>` pagination) | Implemented |

Endpoint status must reflect verified code, not the intended roadmap.

For local registration testing, open `http://127.0.0.1:8000/api/accounts/dev/register/` while Django runs with `DEBUG=True`. Create an invitation in Django Admin first. The form calls the same CSRF-protected registration API as other clients and is unavailable when `DEBUG=False`; it is not the production registration page.

Для локальной проверки регистрации откройте `http://127.0.0.1:8000/api/accounts/dev/register/`, когда Django запущен с `DEBUG=True`. Сначала создайте приглашение в Django Admin. Форма использует тот же API регистрации с защитой CSRF и недоступна при `DEBUG=False`; это не production-страница регистрации.



## Manual verification in Windows PowerShell / Ручная проверка в Windows PowerShell

The following migration command changes the configured local database. It is documented for you to run deliberately; it was not run during this task. Before applying it, confirm `backend/.env` points to the intended development database and make a backup if it contains data you need to retain. Never point this command at production.

Следующая команда миграции изменяет выбранную локальную базу данных. Здесь она приведена для осознанного запуска вами; во время этой задачи она не выполнялась. До запуска проверьте, что `backend/.env` указывает на нужную базу разработки, и сделайте резервную копию важных данных. Не запускайте её для production.

From the repository root, in Terminal 1:

```powershell
if (-not (Test-Path backend\.venv\Scripts\Activate.ps1)) { python -m venv backend\.venv }
.\backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
if (-not (Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
# Review backend\.env and confirm DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT.
python backend\manage.py showmigrations accounts messaging
python backend\manage.py migrate --plan
# Only when you intentionally approve changing the selected local database:
python backend\manage.py migrate
python backend\manage.py check
python backend\manage.py runserver
```

Expected: `migrate --plan` lists the pending account profile and messaging migrations (plus any other unapplied project migrations); after your explicit local run, `showmigrations` marks them `[X]`, `check` reports no issues, and the server listens at `http://127.0.0.1:8000/`. The profile migration adds a profile for existing users with default values. The messaging migration adds empty conversation/message tables. Neither migration deletes or alters existing user, invite, or unrelated application rows. User deletion follows the declared cascade relationships and removes that user's profile/conversations/messages.

Ожидается: `migrate --plan` показывает ожидающие миграции профилей и переписки (а также другие неприменённые миграции проекта); после вашего отдельного запуска `showmigrations` помечает их `[X]`, `check` не находит проблем, сервер слушает `http://127.0.0.1:8000/`. Первая миграция создаёт профили существующим пользователям со значениями по умолчанию. Вторая добавляет пустые таблицы диалогов и сообщений. Они не удаляют и не изменяют существующие строки пользователей, приглашений и несвязанных данных. При удалении пользователя объявленные каскадные связи удаляют его профиль, диалоги и сообщения.

In Terminal 2, from the repository root:

```powershell
Set-Location frontend
if (-not (Test-Path node_modules)) { npm install }
npm run dev
```

Open `http://localhost:3000`. In Django Admin (`http://127.0.0.1:8000/admin/`), sign in with a superuser and create an unused invitation. If needed, create it with `python backend\manage.py createsuperuser` from Terminal 1 while the virtual environment is active.

Manual flow and expected results:

1. Register a second account at `http://localhost:3000/register` with the invitation; it succeeds once, and reuse/invalid invite is rejected. Sign in at `/login`; refreshing restores the session, logout returns to the sign-in screen.
2. Sign in with two accounts in separate browser profiles (or one normal and one private window). In profile settings edit display name, description, and language; reload and sign back in to verify saved profile language is reflected. Avatar controls are not implemented.
3. As account A, start a conversation with account B and send a text message. The dialog appears in the list. Refresh the page: the conversation and message remain. Sign in as B and verify the message is visible and a reply appears for A after refresh.
4. Verify privacy: an unauthenticated browser is redirected to sign-in. Account C, which is not a conversation member, must not be able to retrieve that conversation or its messages; backend returns not found/denied. A user cannot create a conversation with themselves.
5. Change interface language between English and Russian and exercise login, profile, conversation list, and sending. Unsupported first-visit browser language should fall back to English; a manually selected language should persist across reloads. Check a narrow/mobile viewport for usable layout.
6. Open `http://127.0.0.1:8000/api/health/`; expect JSON with `"status": "ok"` and `"database": "connected"`.

Инструкция для ручной проверки:

1. Зарегистрируйте второй аккаунт на `http://localhost:3000/register` по приглашению: регистрация проходит один раз, повторное или неверное приглашение отклоняется. Войдите на `/login`; после обновления страницы сессия восстанавливается, выход возвращает на экран входа.
2. Используйте два аккаунта в отдельных профилях браузера. Под каждым проверьте изменение отображаемого имени, описания и языка; после обновления сохранённые значения остаются. Загрузка аватара не реализована.
3. Под аккаунтом A создайте диалог с B и отправьте текст. Диалог появится в списке; после обновления страницы диалог и сообщение сохраняются. Войдите как B и проверьте, что сообщение видно; отправьте ответ и обновите страницу A.
4. Для проверки приватности создайте третий аккаунт C с отдельным приглашением. Неавторизованный пользователь перенаправляется на вход; аккаунт C не должен получить чужой диалог или сообщения. Нельзя создать диалог с самим собой.
5. Проверьте английский и русский интерфейсы, переключение языка, вход, профиль и переписку. Неподдерживаемый язык браузера при первом посещении должен давать fallback на английский; выбранный язык сохраняется после обновления. Проверьте узкий экран.
6. Откройте `http://127.0.0.1:8000/api/health/`; ожидается JSON со значениями `"status": "ok"` и `"database": "connected"`.

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
- [x] Add temporary cache-based limits for login and registration requests, with tests.

### Stage 3 — Profiles and localization

- [x] Define the user profile model and API.
- [x] Implement profile read/update permissions and language preference synchronization.
- [ ] Implement safe avatar upload, replacement, and deletion.
- [x] Add English and Russian translations for the current prototype interface.
- [x] Implement browser language detection, manual selection, and local persistence for the prototype.
- [x] Synchronize language preference with the user profile after authentication is available.
- [x] Add tests for profile validation and access controls.
- [ ] Manually verify localization fallback in the browser.

### Stage 4 — Private messaging

- [x] Define conversation and message models.
- [x] Implement private one-to-one conversations.
- [x] Implement message history and sending through the API.
- [x] Enforce conversation membership on conversation and message requests.
- [x] Add tests for messaging and access restrictions.

### Stage 5 — Frontend integration

- [x] Replace sample chat data with backend conversations and messages.
- [x] Add Next.js registration and login screens using the Django session API.
- [ ] Verify the frontend authentication flow manually in English and Russian against a running backend.
- [x] Add profile settings (avatar controls remain incomplete).
- [x] Add conversation list and message history.
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

- Avatar upload and management are not implemented.
- Messaging is persistent HTTP-based text messaging; WebSocket realtime delivery, edit/delete, attachments, typing indicators, and read/delivery states are not implemented.
- A separate Django registration test form is available only with `DEBUG=True`; the production-facing registration and login UI is in Next.js.
- Authentication requests have temporary rate limits. Production must configure a shared cache and safe client IP handling at its proxy boundary; distributed attacks and infrastructure-specific controls still need review.
- Profile fields (display name, description, preferred language) are stored per account; avatars are not implemented.
- Localization covers current interface labels; dates, backend responses, and future screens are not fully localized.
- The frontend uses local storage for language preference before sign-in; the authenticated profile preference is synchronized after login.
- Local development defaults to `DEBUG=True`; production must set `DJANGO_DEBUG=False`, a secret `DJANGO_SECRET_KEY`, allowed hosts, exact CORS/CSRF frontend origins, and HTTPS.
- Real-time messaging and attachments are planned.
- End-to-end encryption is not implemented or promised.
- Production hosting and storage have not yet been selected.

## 14. License

No license has been selected yet. Do not assume that the project is open-source or add a license without the owner's decision.
