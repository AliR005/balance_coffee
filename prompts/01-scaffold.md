# 01 · Каркас репозитория

Режим: сначала Plan, после моего OK — Build.
Прочитай `AGENTS.md`, `docs/SPEC.md` (разделы 1, 6, 7), `docs/DESIGN.md` (разделы 2–3), `design/tokens.css`.

## Цель
Монорепо, которое поднимается одной командой, с пустым, но рабочим бэкендом и фронтом, линтерами, тестами и генерацией API-клиента.

## Что сделать

**Корень**
- `docker-compose.yml`: `db` (postgres:16, volume, healthcheck), `api`, `web`. Dev-режим с hot reload.
- `Makefile`: `dev`, `test`, `lint`, `gen-api`, `seed`, `migrate`, `reset-demo` (пока заглушка, печатающая «будет в фазе 09»).
- `.env.example` со всеми переменными: `DATABASE_URL`, `DEFAULT_CURRENCY=RUB`, `CORS_ORIGINS`, `STAFF_TOKEN_SECRET`, `STAFF_TOKEN_TTL_HOURS=12`.
- Минимальный GitHub Actions: lint + test для backend и web.

**backend/**
- uv-проект, Python 3.12. FastAPI с app factory, `GET /health`, настройки через pydantic-settings.
- SQLAlchemy 2 async, сессии через dependency, Alembic с async-окружением, базовая модель (id, created_at, updated_at).
- Единый формат ошибок `{code, message, details}` и `request_id` в ответах и логах.
- Структурные логи в JSON.
- pytest + pytest-asyncio; тестовая БД отдельная (`_test`), схема поднимается миграциями. Один тест на `/health` и один интеграционный тест на подключение к БД.
- ruff (lint + format), mypy strict для `app/`.
- Скрипт `backend/scripts/export_openapi.py`, пишет `web/openapi.json`.

**web/**
- Vite + React + TypeScript (strict), Tailwind v4, shadcn/ui (init, но пока без компонентов), React Router, TanStack Query, Zustand, Framer Motion.
- Шрифт Onest локально через `@fontsource/onest` (cyrillic + latin, веса 400/500/600/700).
- Скопируй `design/tokens.css` в `web/src/shared/styles/tokens.css`, подключи и замапь токены на тему Tailwind (`@theme`), чтобы в компонентах были доступны классы вроде `bg-surface`, `text-text-2`, `rounded-card`. Никаких значений цветов вне tokens.css.
- Словарь `web/src/shared/i18n` (ru), хук `useT()`.
- orval: генерация клиента из `web/openapi.json` в `web/src/shared/api/generated`, `make gen-api` делает всё за один шаг.
- vitest, eslint, prettier. Один пример-тест.
- Страница-заглушка `/`, которая вызывает `/health` через сгенерированный клиент и показывает результат.

## Границы (не делай)
Никаких моделей предметной области, экранов, компонентов UI, авторизации, PWA, деплоя.

## Критерии готовности
- `cp .env.example .env && make dev` поднимает db, api, web.
- `make lint` и `make test` зелёные.
- `make gen-api` создаёт клиент без ручных правок; заглушка на `/` показывает статус API.
- Токены подключены, переключение `data-theme` меняет фон и текст.

Отчёт по формату из AGENTS.md.
