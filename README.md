# DevChat

**Русский** | [English](#english)

---

# Русская версия

## О проекте

**DevChat** — приватное веб-приложение для обмена сообщениями в небольшой группе друзей. Проект разрабатывается как full-stack приложение с отдельными frontend и backend, регистрацией по приглашениям и личными переписками.

Основные цели проекта:

- Закрытая регистрация пользователей по приглашениям.
- Личные переписки между пользователями.
- Простой адаптивный интерфейс.
- Обмен сообщениями в реальном времени.
- Передача изображений и файлов.
- Безопасная работа с учётными записями и личными сообщениями.

## Технологический стек

**Frontend**
- Next.js
- React
- JavaScript
- CSS Modules

**Backend**
- Python
- Django
- Django REST Framework
- Django Channels — запланированная интеграция WebSocket

**База данных и инфраструктура**
- PostgreSQL 18
- Redis — при необходимости для WebSocket-инфраструктуры
- Переменные окружения для конфигурации и секретов

## Архитектура проекта

```text
DevChat/
├── backend/
│   ├── accounts/
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── config/
│   ├── core/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                 # локальный файл, не коммитится
├── frontend/
│   ├── app/
│   │   ├── lib/
│   │   │   └── api.js
│   │   ├── page.js
│   │   ├── page.module.css
│   │   └── globals.css
│   ├── package.json
│   └── ...
├── .gitignore
├── AGENTS.md
└── README.md
```

- `backend/` — Django, API и работа с базой данных.
- `backend/accounts/` — регистрация пользователей и управление инвайт-кодами.
- `backend/core/` — базовые endpoints, включая проверку состояния backend.
- `frontend/` — пользовательский интерфейс на Next.js.
- `frontend/app/lib/api.js` — клиент для обращения к Django API.
- `.env` — локальные настройки и секреты, которые нельзя публиковать.
- `.env.example` — шаблон необходимых переменных окружения без реальных секретов.

## Реализованная функциональность

- Инициализированы frontend и backend.
- Настроено подключение Django к PostgreSQL.
- Реализована проверка состояния backend и соединения с базой данных.
- Настроен CORS для локальной разработки.
- Создан интерфейс чата с переключением между диалогами и отправкой сообщений в локальном состоянии frontend.
- Подключён frontend к endpoint проверки состояния Django.
- Добавлена модель инвайт-кодов и управление ими через Django Admin.
- Реализована регистрация по имени пользователя, паролю и инвайт-коду.
- Пароли сохраняются с использованием встроенного механизма хеширования Django.
- Использованный инвайт-код автоматически помечается как недоступный для повторного использования.
- Повторное использование инвайта отклоняется.
- Создание пользователя и использование инвайта выполняются в одной транзакции.

**Ограничение:** сообщения интерфейса пока не сохраняются в PostgreSQL. Полноценная авторизация и личные переписки между реальными аккаунтами ещё не реализованы.

## Текущий статус

### Wave 1 — Фундамент проекта

**Выполнено**
- [x] Создан Git-репозиторий.
- [x] Созданы и отправлены на GitHub ветки `main` и `dev`.
- [x] Инициализирован Django-проект.
- [x] Создана база данных PostgreSQL `devchat_db`.
- [x] Настроено чтение конфигурации из `.env`.
- [x] Применены миграции Django.
- [x] Создано приложение `core`.
- [x] Реализован `GET /api/health/`.
- [x] Настроен CORS для локального frontend.
- [x] Создан `backend/requirements.txt`.
- [x] Создан `backend/.env.example`.
- [x] Инициализирован Next.js frontend.
- [x] Создан базовый интерфейс чата.
- [x] Проверено подключение frontend к Django и PostgreSQL.

### Wave 2 — Пользователи и приглашения

**Выполнено**
- [x] Создано приложение `accounts`.
- [x] Добавлена модель `InviteCode`.
- [x] Подключено управление инвайтами через Django Admin.
- [x] Реализована проверка доступности инвайт-кода.
- [x] Реализован `POST /api/accounts/register/`.
- [x] Добавлена проверка уникальности имени пользователя.
- [x] Реализовано создание пользователя с хешированием пароля.
- [x] Добавлена автоматическая отметка использованного инвайта.
- [x] Проверено, что использованный код нельзя применить повторно.

**Осталось**
- [ ] Реализовать API входа в аккаунт.
- [ ] Настроить JWT-аутентификацию или другой выбранный механизм авторизации.
- [ ] Защитить API личных данных авторизацией и проверкой прав доступа.
- [ ] Добавить автоматизированные тесты регистрации и авторизации.
- [ ] Создать frontend-формы регистрации и входа.

### Wave 3 — Переписки и сообщения

- [ ] Создать модели переписок и участников.
- [ ] Создать модель сообщений и API endpoints.
- [ ] Ограничить доступ к перепискам только их участниками.
- [ ] Реализовать сохранение истории сообщений и пагинацию.
- [ ] Добавить редактирование, удаление, ответы и реакции.

### Wave 4 — Интеграция интерфейса

- [ ] Создать страницы регистрации и входа.
- [ ] Подключить список переписок к backend.
- [ ] Подключить интерфейс чата к реальным сообщениям.
- [ ] Реализовать адаптивную вёрстку.
- [ ] Добавить светлую и тёмную темы.
- [ ] Обработать состояния загрузки, отсутствия данных и ошибок.

### Wave 5 — Реальное время и вложения

- [ ] Интегрировать Django Channels.
- [ ] Реализовать аутентификацию WebSocket и проверку прав доступа.
- [ ] Добавить доставку сообщений в реальном времени.
- [ ] Добавить индикаторы набора текста, доставки и прочтения.
- [ ] Реализовать загрузку изображений и файлов.
- [ ] Подключить Redis, если он потребуется для выбранной конфигурации.

### Wave 6 — Тестирование и развёртывание

- [ ] Добавить тесты backend и frontend.
- [ ] Проверить авторизацию, права доступа и безопасность загрузки файлов.
- [ ] Подготовить production-конфигурацию.
- [ ] Настроить production-базу данных и хранение файлов.
- [ ] Развернуть приложение.
- [ ] Документировать запуск и обслуживание.

## Локальный запуск

### Требования

Установите:
- Git.
- Python, совместимый с зависимостями backend.
- Node.js и npm.
- PostgreSQL 18.
- Редактор кода, например Visual Studio Code.

Redis не требуется для начального REST API.

### 1. Клонирование репозитория

```bash
git clone https://github.com/count-rzy/DevChat.git
cd DevChat
git switch dev
```

### 2. Настройка backend

Из корня проекта:

```powershell
python -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
```

### 3. Настройка переменных окружения

Создайте локальный `.env` на основе шаблона:

```powershell
Copy-Item backend/.env.example backend/.env
```

Заполните `backend/.env` параметрами локальной базы данных:

```dotenv
DB_NAME=devchat_db
DB_USER=postgres
DB_PASSWORD=your_local_database_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

Замените пример пароля своим локальным паролем PostgreSQL.

**Не добавляйте `.env` в Git и не публикуйте его содержимое.**

### 4. Подготовка базы данных

Создайте PostgreSQL-базу `devchat_db`, если она ещё не существует.

Примените миграции:

```powershell
python backend/manage.py migrate
```

### 5. Запуск backend

```powershell
python backend/manage.py runserver
```

По умолчанию Django доступен по адресу `http://127.0.0.1:8000/`.

### 6. Проверка backend

Откройте:

`http://127.0.0.1:8000/api/health/`

Ожидаемый ответ при успешном подключении:

```json
{
  "status": "ok",
  "database": "connected"
}
```

### 7. Запуск frontend

Откройте второй терминал из корня проекта:

```powershell
cd frontend
npm install
npm run dev
```

По умолчанию frontend доступен по адресу `http://localhost:3000/`.

Для локальной разработки frontend обращается к Django API по адресу `http://127.0.0.1:8000/api`, если не задана переменная `NEXT_PUBLIC_API_URL`.

## API

### Реализованные endpoints

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/api/health/` | Проверка API и подключения к базе данных |
| `POST` | `/api/accounts/register/` | Регистрация пользователя по инвайту |

Регистрация принимает JSON:

```json
{
  "username": "example_user",
  "password": "a-strong-password",
  "invite_code": "your-invite-code"
}
```

При успешной регистрации возвращается HTTP `201 Created`. Неверный или использованный инвайт приводит к HTTP `400 Bad Request`.

### Планируемые области API

| Область | Назначение |
|---|---|
| Accounts | Регистрация, вход и данные пользователей |
| Invitations | Управление и проверка кодов приглашений |
| Conversations | Личные переписки и участники |
| Messages | История и управление сообщениями |
| Attachments | Загрузка изображений и файлов |

Запланированные endpoints не считаются реализованными до завершения разработки и проверки.

## Правила разработки

Используются следующие Git-ветки:

- `main` — стабильная версия проекта.
- `dev` — интеграционная ветка разработки.
- `feature/<name>` — отдельная функция или задача.

Рекомендуемый процесс:

1. Обновить локальную ветку `dev`.
2. Создать feature-ветку от `dev`.
3. Реализовать одну логически завершённую задачу.
4. Запустить проверки и тесты.
5. Создать коммит с понятным сообщением.
6. Отправить ветку на GitHub.
7. Создать Pull Request в `dev`.
8. Объединить изменения после проверки.

Пример:

```bash
git switch dev
git pull origin dev
git switch -c feature/login
```

Не отправляйте обычные рабочие изменения напрямую в `main`.

## Безопасность и качество кода

- Храните пароли, токены и секретные ключи в переменных окружения.
- Не коммитьте `.env` и другие файлы с секретами.
- Проверяйте данные на backend, даже если frontend выполняет валидацию.
- Проверяйте права доступа при каждой операции с личными переписками и сообщениями.
- Используйте встроенные механизмы Django для хеширования паролей.
- Ограничивайте CORS явно разрешёнными источниками.
- Проверяйте тип и размер загружаемых файлов.
- Не раскрывайте чувствительные данные в API-ответах и логах.
- Добавляйте тесты для важных бизнес-правил и проверки разрешений.
- Используйте HTTPS и безопасную конфигурацию при production-развёртывании.

## Текущие ограничения

DevChat находится в активной разработке. Регистрация по инвайтам и базовая интеграция frontend с backend работают, однако полноценная авторизация, хранение сообщений, личные переписки между реальными аккаунтами и обмен сообщениями в реальном времени ещё не реализованы.

Наличие интерфейса чата не означает, что сообщения уже сохраняются в базе данных.

## Лицензия

Лицензия проекта пока не выбрана. Все права сохраняются за правообладателем, пока в репозитории не будет добавлена лицензия.

---

# English

## About

**DevChat** is a private messaging web application designed for a small group of friends. It is developed as a full-stack project with a separate frontend and backend, invite-only registration, and private conversations.

Project goals:

- Invite-only user registration.
- Private one-to-one conversations.
- A clean, responsive interface.
- Real-time message delivery.
- Image and file sharing.
- Secure handling of user accounts and private messages.

## Technology Stack

**Frontend**
- Next.js
- React
- JavaScript
- CSS Modules

**Backend**
- Python
- Django
- Django REST Framework
- Django Channels — planned WebSocket integration

**Database and Infrastructure**
- PostgreSQL 18
- Redis if required by the WebSocket infrastructure
- Environment variables for configuration and secrets

## Project Architecture

```text
DevChat/
├── backend/
│   ├── accounts/
│   │   ├── migrations/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── config/
│   ├── core/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                 # local only, never committed
├── frontend/
│   ├── app/
│   │   ├── lib/
│   │   │   └── api.js
│   │   ├── page.js
│   │   ├── page.module.css
│   │   └── globals.css
│   ├── package.json
│   └── ...
├── .gitignore
├── AGENTS.md
└── README.md
```

- `backend/` contains the Django application, API, and database integration.
- `backend/accounts/` handles registration and invitation codes.
- `backend/core/` contains core endpoints, including the backend health check.
- `frontend/` contains the Next.js user interface.
- `frontend/app/lib/api.js` provides the frontend API client.
- `.env` stores local configuration and secrets and must not be committed.
- `.env.example` documents required environment variables without exposing real credentials.

## Implemented Features

- Initialized the frontend and backend.
- Configured Django to connect to PostgreSQL.
- Implemented a backend health check that verifies database connectivity.
- Configured CORS for local development.
- Built a chat interface with conversation switching and locally managed messages.
- Connected the frontend to the Django health endpoint.
- Added the `InviteCode` model and Django Admin management.
- Implemented registration using a username, password, and invitation code.
- Used Django's built-in password hashing.
- Automatically marked invitation codes as used after successful registration.
- Rejected attempts to reuse an invitation code.
- Created the user and marked the invitation as used within a single database transaction.

**Limitation:** Chat messages are not yet persisted in PostgreSQL. Full authentication and private conversations between real accounts have not been implemented.

## Project Status

### Wave 1 — Foundation

**Completed**
- [x] Git repository initialized.
- [x] `main` and `dev` branches created and pushed to GitHub.
- [x] Django project initialized.
- [x] PostgreSQL database `devchat_db` created.
- [x] Environment-based configuration added.
- [x] Django migrations applied.
- [x] `core` application created.
- [x] `GET /api/health/` endpoint implemented.
- [x] CORS configured for local frontend development.
- [x] `backend/requirements.txt` created.
- [x] `backend/.env.example` created.
- [x] Next.js frontend initialized.
- [x] Basic chat interface implemented.
- [x] Frontend connection to Django and PostgreSQL verified.

### Wave 2 — Accounts and Invitations

**Completed**
- [x] `accounts` application created.
- [x] `InviteCode` model added.
- [x] Invitation management integrated with Django Admin.
- [x] Invitation-code availability validation implemented.
- [x] `POST /api/accounts/register/` implemented.
- [x] Username uniqueness validation added.
- [x] User creation with password hashing implemented.
- [x] Used invitation codes are automatically marked as unavailable.
- [x] Reuse of invitation codes tested and rejected.

**Remaining**
- [ ] Implement the login API.
- [ ] Configure JWT authentication or another selected authentication mechanism.
- [ ] Protect private API data with authentication and authorization checks.
- [ ] Add automated registration and authentication tests.
- [ ] Build frontend registration and login forms.

### Wave 3 — Conversations and Messages

- [ ] Create conversation and membership models.
- [ ] Create message models and API endpoints.
- [ ] Restrict conversation access to participants.
- [ ] Implement message history and pagination.
- [ ] Add editing, deletion, replies, and reactions.

### Wave 4 — Frontend Integration

- [ ] Build registration and login pages.
- [ ] Connect the conversation list to the backend.
- [ ] Connect the chat interface to real messages.
- [ ] Implement responsive layouts.
- [ ] Add dark and light themes.
- [ ] Handle loading, empty, and error states.

### Wave 5 — Real-Time Communication and Attachments

- [ ] Integrate Django Channels.
- [ ] Implement WebSocket authentication and access checks.
- [ ] Add real-time message delivery.
- [ ] Add typing indicators and delivery/read statuses.
- [ ] Implement image and file uploads.
- [ ] Add Redis if required by the selected channel-layer configuration.

### Wave 6 — Testing and Deployment

- [ ] Add backend and frontend tests.
- [ ] Review authentication, permissions, and file-upload security.
- [ ] Prepare production configuration.
- [ ] Configure production database and file storage.
- [ ] Deploy the application.
- [ ] Document deployment and maintenance.

## Getting Started

### Prerequisites

Install:
- Git.
- Python compatible with the backend dependencies.
- Node.js and npm.
- PostgreSQL 18.
- A code editor such as Visual Studio Code.

Redis is not required for the initial REST API.

### 1. Clone the Repository

```bash
git clone https://github.com/count-rzy/DevChat.git
cd DevChat
git switch dev
```

### 2. Set Up the Backend

From the project root:

```powershell
python -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables

Create a local `.env` file from the example:

```powershell
Copy-Item backend/.env.example backend/.env
```

Configure `backend/.env` with your local PostgreSQL credentials:

```dotenv
DB_NAME=devchat_db
DB_USER=postgres
DB_PASSWORD=your_local_database_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

Replace the example password with your local PostgreSQL password.

**Never commit `.env` or publish its contents.**

### 4. Prepare the Database

Create a PostgreSQL database named `devchat_db` if it does not already exist.

Apply Django migrations:

```powershell
python backend/manage.py migrate
```

### 5. Start the Backend

```powershell
python backend/manage.py runserver
```

By default, Django is available at `http://127.0.0.1:8000/`.

### 6. Verify the Backend

Open:

`http://127.0.0.1:8000/api/health/`

Expected response when the API and database are available:

```json
{
  "status": "ok",
  "database": "connected"
}
```

### 7. Start the Frontend

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

By default, the frontend is available at `http://localhost:3000/`.

For local development, the frontend uses `http://127.0.0.1:8000/api` unless `NEXT_PUBLIC_API_URL` is configured.

## API

### Implemented Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health/` | Check API and database connectivity |
| `POST` | `/api/accounts/register/` | Register a user with an invitation code |

Registration accepts JSON:

```json
{
  "username": "example_user",
  "password": "a-strong-password",
  "invite_code": "your-invite-code"
}
```

Successful registration returns HTTP `201 Created`. An invalid or previously used invitation code returns HTTP `400 Bad Request`.

### Planned API Areas

| Area | Responsibility |
|---|---|
| Accounts | Registration, login, and user information |
| Invitations | Invitation-code management and validation |
| Conversations | Private conversations and participants |
| Messages | Message history and message operations |
| Attachments | Image and file uploads |

Planned endpoints are not considered implemented until development and verification are complete.

## Development Workflow

The repository uses the following branches:

- `main` — stable project version.
- `dev` — development integration branch.
- `feature/<name>` — an individual feature or task.

Recommended workflow:

1. Update the local `dev` branch.
2. Create a feature branch from `dev`.
3. Implement one focused change.
4. Run relevant checks and tests.
5. Commit with a descriptive message.
6. Push the branch to GitHub.
7. Open a pull request targeting `dev`.
8. Merge after review and verification.

Example:

```bash
git switch dev
git pull origin dev
git switch -c feature/login
```

Do not push regular development changes directly to `main`.

## Security and Code Quality

- Keep passwords, tokens, and secret keys in environment variables.
- Never commit `.env` or other files containing secrets.
- Validate input on the backend, even when the frontend also validates it.
- Enforce authorization for every private conversation and message operation.
- Use Django's built-in password hashing mechanisms.
- Restrict CORS to explicitly allowed origins.
- Validate uploaded file types and sizes.
- Avoid exposing sensitive data in API responses and logs.
- Add tests for important business rules and access-control checks.
- Use HTTPS and production-grade configuration when deploying.

## Current Limitations

DevChat is under active development. Invite-only registration and basic frontend-to-backend integration are working, but full authentication, message persistence, private conversations between real accounts, and real-time messaging have not yet been implemented.

The presence of a chat interface does not mean messages are already stored in the database.

## License

No license has been selected yet. All rights are reserved unless a license is added to the repository.