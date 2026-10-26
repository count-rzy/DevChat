# DevChat

**Русский** | [English](#english)

---

# Русская версия

## О проекте

**DevChat** — приватное веб-приложение для обмена сообщениями в небольшой группе друзей. Проект разрабатывается как full-stack приложение с отдельными frontend и backend, поддержкой личных переписок и обмена сообщениями в реальном времени.

Основные цели проекта:
- Закрытая регистрация пользователей по приглашениям.
- Личные переписки между пользователями.
- Простой и адаптивный интерфейс.
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
- Django Channels для WebSocket-соединений

**База данных и инфраструктура**
- PostgreSQL 18
- Redis при необходимости для WebSocket-инфраструктуры
- Переменные окружения для конфигурации и секретов

## Архитектура проекта

```text
DevChat/
├── backend/
│   ├── config/
│   ├── core/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── frontend/
├── .gitignore
└── README.md
```

- `backend/` — Django, API и работа с базой данных.
- `frontend/` — интерфейс приложения на Next.js.
- `.env` — локальные настройки и секреты, которые нельзя публиковать.
- `.env.example` — шаблон необходимых переменных окружения без реальных секретов.

Структура будет расширяться по мере реализации авторизации, переписок, сообщений и WebSocket-соединений.

## Функциональность

### Запланировано

- Регистрация по приглашению: имя пользователя, пароль и код приглашения.
- Авторизация пользователей.
- Личные переписки один на один.
- История сообщений.
- Редактирование и удаление сообщений.
- Ответы на сообщения и реакции.
- Статусы доставки и прочтения.
- Индикатор набора текста.
- Отправка изображений и файлов.
- Адаптивный интерфейс для компьютеров и мобильных устройств.
- Светлая и тёмная темы.

Функции будут добавляться поэтапно. Запланированная возможность не считается реализованной до завершения разработки и проверки.

## Текущий статус

### Wave 1 — Фундамент проекта

**Выполнено**
- [x] Создан Git-репозиторий.
- [x] Созданы и отправлены на GitHub ветки `main` и `dev`.
- [x] Инициализирован Django-проект.
- [x] Создана база данных PostgreSQL `devchat_db`.
- [x] Настроено чтение конфигурации из `.env`.
- [x] Применены начальные миграции Django.
- [x] Создано приложение `core`.
- [x] Реализован `GET /api/health/` для проверки API и подключения к базе данных.
- [x] Настроен CORS для локальной разработки frontend.
- [x] Создан `backend/requirements.txt`.
- [x] Создан `backend/.env.example`.

**В работе**
- [ ] Проверка установки backend в чистом окружении.
- [ ] Инициализация Next.js frontend.
- [ ] Подключение frontend к Django API.
- [ ] Проверка CORS реальным запросом из frontend.
- [ ] Добавление базовых автоматизированных тестов.

### Wave 2 — Пользователи и приглашения

- [ ] Настройка модели пользователя и авторизации.
- [ ] Проверка кодов приглашений.
- [ ] Реализация регистрации и входа.
- [ ] Проверка аутентификации и прав доступа.
- [ ] Тестирование неверных учётных данных и неавторизованных запросов.

### Wave 3 — Переписки и сообщения

- [ ] Создание моделей переписок и участников.
- [ ] Создание модели сообщений и API endpoints.
- [ ] Ограничение доступа к перепискам только их участниками.
- [ ] История сообщений и пагинация.
- [ ] Редактирование, удаление, ответы и реакции.

### Wave 4 — Интерфейс

- [ ] Страницы регистрации и входа.
- [ ] Список переписок.
- [ ] Интерфейс личного чата.
- [ ] Адаптивная вёрстка.
- [ ] Светлая и тёмная темы.
- [ ] Состояния загрузки, отсутствия данных и ошибок.

### Wave 5 — Реальное время и вложения

- [ ] Интеграция Django Channels.
- [ ] Аутентификация WebSocket-соединений и проверка прав доступа.
- [ ] Доставка сообщений в реальном времени.
- [ ] Индикаторы набора текста, доставки и прочтения.
- [ ] Загрузка изображений и файлов.
- [ ] Подключение Redis, если он потребуется для выбранной конфигурации.

### Wave 6 — Тестирование и развёртывание

- [ ] Тесты backend и frontend.
- [ ] Проверка авторизации, разрешений и безопасности загрузки файлов.
- [ ] Подготовка production-конфигурации.
- [ ] Настройка production-базы данных и хранения файлов.
- [ ] Развёртывание приложения.
- [ ] Документация по запуску и обслуживанию.

## Локальный запуск

### Требования

Необходимо установить:
- Git.
- Python, совместимый с зависимостями backend.
- Node.js и npm.
- PostgreSQL 18.
- Редактор кода, например Visual Studio Code.

Redis не требуется для начального REST API. Он может понадобиться при реализации обмена сообщениями в реальном времени.

### 1. Клонирование репозитория

```bash
git clone https://github.com/count-rzy/DevChat.git
cd DevChat
git switch dev
```

### 2. Настройка backend

Перейдите в папку backend:

```bash
cd backend
```

Создайте виртуальное окружение:

```bash
python -m venv .venv
```

Активируйте его в PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Установите зависимости:

```bash
python -m pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте `.env` на основе шаблона:

```powershell
Copy-Item .env.example .env
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

Создайте базу `devchat_db`, если она ещё не существует.

Примените миграции:

```bash
python manage.py migrate
```

### 5. Запуск сервера

```bash
python manage.py runserver
```

По умолчанию Django будет доступен по адресу `http://127.0.0.1:8000/`.

### 6. Проверка API

Откройте:

`http://127.0.0.1:8000/api/health/`

Ожидаемый ответ при успешном подключении:

```json
{
  "status": "ok",
  "database": "connected"
}
```

Этот endpoint предназначен для проверки работоспособности во время разработки и не заменяет полноценный production-мониторинг.

### 7. Настройка frontend

Инструкция по запуску frontend будет добавлена после инициализации Next.js-приложения и фиксации его зависимостей.

## API

Реализованный endpoint:

| Метод | Адрес | Назначение |
|---|---|---|
| `GET` | `/api/health/` | Проверка API и подключения к базе данных |

Планируемые области API:

| Область | Назначение |
|---|---|
| Accounts | Регистрация, вход и данные пользователей |
| Invitations | Проверка кодов приглашений |
| Conversations | Личные переписки и участники |
| Messages | История и управление сообщениями |
| Attachments | Загрузка изображений и файлов |

Перечисленные выше области API пока являются планом, если они отдельно не отмечены как реализованные.

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
git switch -c feature/wave-1-foundation
```

Не отправляйте обычные рабочие изменения напрямую в `main`.

## Безопасность и качество кода

- Храните пароли, токены и секретные ключи в переменных окружения.
- Не коммитьте `.env` и другие файлы с секретами.
- Проверяйте данные на backend, даже если frontend уже выполняет валидацию.
- Проверяйте права доступа при каждой операции с личными переписками и сообщениями.
- Используйте встроенные механизмы Django для хеширования паролей.
- Не разрешайте CORS-запросы с произвольных сайтов.
- Проверяйте тип и размер загружаемых файлов.
- Не раскрывайте чувствительные данные в API-ответах и логах.
- Добавляйте тесты для важных бизнес-правил и проверки разрешений.
- Фиксируйте зависимости проекта.
- Используйте HTTPS и безопасную конфигурацию при production-развёртывании.

## Текущее состояние проекта

DevChat находится в активной разработке. Базовая конфигурация backend и подключение PostgreSQL готовы, но полноценное приложение для обмена сообщениями ещё не реализовано.

Регистрация, приглашения, переписки, обмен сообщениями, вложения и frontend будут реализованы в следующих этапах.

## Лицензия

Лицензия проекта пока не выбрана. Все права сохраняются за правообладателем, пока в репозитории не будет добавлена лицензия.

---

# English

## About

**DevChat** is a private messaging web application designed for a small group of friends. It is developed as a full-stack project with a separate frontend and backend, private conversations, and real-time messaging.

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
- Django Channels for WebSocket communication

**Database and Infrastructure**
- PostgreSQL 18
- Redis if required for the WebSocket infrastructure
- Environment variables for configuration and secrets

## Project Architecture

```text
DevChat/
├── backend/
│   ├── config/
│   ├── core/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── frontend/
├── .gitignore
└── README.md
```

- `backend/` contains the Django application, API, and database integration.
- `frontend/` will contain the Next.js user interface.
- `.env` stores local configuration and secrets and must not be committed.
- `.env.example` documents required environment variables without exposing real credentials.

The structure will expand as authentication, conversations, messages, and WebSocket communication are implemented.

## Planned Features

- Invite-only registration using a username, password, and invitation code.
- User authentication.
- Private one-to-one conversations.
- Message history.
- Message editing and deletion.
- Replies and reactions.
- Delivery and read statuses.
- Typing indicators.
- Image and file attachments.
- Responsive desktop and mobile layouts.
- Dark and light themes.

Features will be implemented incrementally. A planned feature is not considered complete until it has been implemented and verified.

## Project Status

### Wave 1 — Foundation

**Completed**
- [x] Git repository initialized.
- [x] `main` and `dev` branches created and pushed to GitHub.
- [x] Django project initialized.
- [x] PostgreSQL database `devchat_db` created.
- [x] Environment-based configuration added.
- [x] Initial Django migrations applied.
- [x] `core` application created.
- [x] `GET /api/health/` endpoint implemented to check API and database availability.
- [x] CORS configured for local frontend development.
- [x] `backend/requirements.txt` created.
- [x] `backend/.env.example` created.

**In progress**
- [ ] Verify backend setup from a clean environment.
- [ ] Initialize the Next.js frontend.
- [ ] Connect the frontend to the Django API.
- [ ] Verify CORS with an actual frontend request.
- [ ] Add basic automated tests.

### Wave 2 — Accounts and Invitations

- [ ] Configure the user model and authentication.
- [ ] Implement invitation-code validation.
- [ ] Implement registration and login endpoints.
- [ ] Add authentication and authorization checks.
- [ ] Test invalid credentials and unauthorized requests.

### Wave 3 — Conversations and Messages

- [ ] Create conversation and membership models.
- [ ] Create message models and API endpoints.
- [ ] Restrict conversation access to its participants.
- [ ] Implement message history and pagination.
- [ ] Add editing, deletion, replies, and reactions.

### Wave 4 — Frontend Interface

- [ ] Build registration and login screens.
- [ ] Build the conversation list.
- [ ] Build the private chat interface.
- [ ] Implement responsive layouts.
- [ ] Add dark and light themes.
- [ ] Add loading, empty, and error states.

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
- [ ] Configure the production database and file storage.
- [ ] Deploy the application.
- [ ] Document deployment and maintenance.

## Getting Started

### Prerequisites

Install the following tools:
- Git.
- Python compatible with the backend dependencies.
- Node.js and npm.
- PostgreSQL 18.
- A code editor such as Visual Studio Code.

Redis is not required for the initial REST API. It may be needed when real-time messaging is implemented.

### 1. Clone the Repository

```bash
git clone https://github.com/count-rzy/DevChat.git
cd DevChat
git switch dev
```

### 2. Set Up the Backend

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Configure `backend/.env` with your local PostgreSQL credentials:

```dotenv
DB_NAME=devchat_db
DB_USER=postgres
DB_PASSWORD=your_local_database_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

Replace the example password with your actual local PostgreSQL password.

**Never commit `.env` or publish its contents.**

### 4. Prepare the Database

Create a PostgreSQL database named `devchat_db` if it does not already exist.

Apply Django migrations:

```bash
python manage.py migrate
```

### 5. Start the Backend

```bash
python manage.py runserver
```

By default, Django is available at `http://127.0.0.1:8000/`.

### 6. Verify the API

Open:

`http://127.0.0.1:8000/api/health/`

Expected response when the API and database are available:

```json
{
  "status": "ok",
  "database": "connected"
}
```

This endpoint is intended for development checks and does not replace production monitoring.

### 7. Set Up the Frontend

Frontend setup instructions will be added after the Next.js application has been initialized and its dependencies have been documented.

## API Overview

Implemented endpoint:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health/` | Check API and database availability |

Planned API areas:

| Area | Responsibility |
|---|---|
| Accounts | Registration, login, and user information |
| Invitations | Invitation-code validation |
| Conversations | Private conversations and participants |
| Messages | Message history and message operations |
| Attachments | Image and file uploads |

These API areas are planned and are not implemented unless explicitly marked as completed.

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
6. Push the feature branch to GitHub.
7. Open a pull request targeting `dev`.
8. Merge after review and verification.

Example:

```bash
git switch dev
git pull origin dev
git switch -c feature/wave-1-foundation
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
- Keep dependencies documented and reproducible.
- Use HTTPS and production-grade configuration when deploying.

## Current Limitations

DevChat is under active development. The backend foundation and PostgreSQL connection are in place, but the complete messaging application has not yet been implemented.

Authentication, invitations, private conversations, messaging, attachments, and the frontend remain planned work.

## License

No license has been selected yet. All rights are reserved unless a license is added to the repository.
