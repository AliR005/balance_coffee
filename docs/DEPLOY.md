# DEPLOY — поднятие демо на VPS

## Что нужно
- VPS с Docker и Compose v2, домен с A-записью на VPS, открытые 80/443.

## Шаги
1. Склонируй репозиторий на сервер, перейди в корень.
2. Создай продовый `.env` (секретов в репозитории нет):
   ```bash
   cp .env.example .env.prod
   ```
   Заполни в `.env.prod`: `DOMAIN` (твой домен), `POSTGRES_PASSWORD` (длинный случайный),
   `STAFF_TOKEN_SECRET` (длинный случайный), `DEFAULT_CURRENCY=RUB`,
   `CORS_ORIGINS=https://ТВОЙ-ДОМЕН`.
3. Подними прод-стек (Caddy сам выпустит HTTPS):
   ```bash
   docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
   ```
   Entrypoint api-контейнера сам дождётся БД, накатит миграции и засеет демо-данные.
4. Проверь: `https://ТВОЙ-ДОМЕН/health` — API напрямую недоступен снаружи, только через Caddy:
   - `https://ТВОЙ-ДОМЕН/` — приложение;
   - `https://ТВОЙ-ДОМЕН/api/locations` — API через прокси.
5. PIN баристы — из seed (`backend/seed/menu.yaml`, поля `staff_pin`, только для демо).

## Бэкап БД
```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml exec db \
  pg_dump -U balance balance > backup-$(date +%F).sql
```

## Обновление
```bash
git pull
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```
Миграции накатятся сами при старте api. Откат — предыдущий коммит + та же команда.

## Лимиты и заголовки
- Caddy ставит security-заголовки и проксирует `/api` без буферизации (SSE).
- API ограничивает `POST /orders` (60/мин с IP) и попытки `/staff/login` (10/5 мин на точку).
