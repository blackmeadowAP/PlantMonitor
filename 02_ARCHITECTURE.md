# 02. Архитектура

## Компоненты (Docker Compose)

| Сервис | Образ / код | Назначение |
| --- | --- | --- |
| `bot` | `python -m bot` | aiogram 3, long polling. Диалоги, приём фото, геопроверка. Тонкие хэндлеры → `core/services` |
| `api` | `uvicorn api.main:app` | FastAPI: данные для Mini App, проверка Telegram initData, раздача `webapp/` |
| `worker` | `arq worker.main.WorkerSettings` | Фоновые задачи: обработка фото, ИИ-подсказки, расчёт показателей, отчёты, рассылки; cron через APScheduler |
| `db` | `postgis/postgis:16-3.4` | PostgreSQL + PostGIS |
| `redis` | `redis:7` | FSM бота, очередь arq |
| `minio` | `minio/minio` | Локальное S3 (только разработка; в пилоте заменяется на R2 через .env) |
| `ollama` | `ollama/ollama` | Локальная языковая модель (шаг 12, опционально) |
| `tunnel` | `cloudflare/cloudflared` | HTTPS для Mini App (шаг 10, пилот) |

Образ приложения один (`app`), сервисы `bot`, `api`, `worker` отличаются командой запуска.

## Потоки данных

1. **Фото:** Telegram → `bot` (скачивание через getFile, ≤ 20 МБ) → проверка качества и геопозиции → копия оригинала в архивный канал (`copy_message`) → рабочая копия 1600 px JPEG q85 в S3 → записи `observations` и `photos` → задача в очередь `predict_photo` (если `ML_MODE != off`).
2. **Разметка:** агроном в `bot` → `assessments` (+ `foci`, `focus_updates`) → задача `recalc_field_stats(field_id, date)`.
3. **Показатели:** `worker` пересчитывает `daily_field_stats` и `daily_user_stats` при событиях и по cron в 17:45.
4. **Отчёты:** cron 18:00 (предприятия) и 19:00 (область) → факты (SQL) → [LLM-резюме] → Jinja2 → WeasyPrint → PDF в S3 → отправка в чат.
5. **Карта:** Mini App → `api` (initData → пользователь → права) → GeoJSON предприятий/полей/очагов.

## Структура репозитория

```text
agro-monitor/
  AGENTS.md  README.md  .env.example  pyproject.toml  docker-compose.yml  Dockerfile
  docs/
  core/
    config.py          # pydantic-settings
    db.py              # engine, session
    models/            # SQLAlchemy-модели (по файлу на группу таблиц)
    services/          # бизнес-логика: users, fields, tasks, observations, assessments, stats, reports, access
    geo.py             # расстояния, проверки точек
    images.py          # сжатие, резкость, яркость
    storage.py         # S3 + архивный канал
  bot/
    __main__.py  texts.py  keyboards.py  states.py  middlewares.py
    handlers/          # common.py, worker.py, agronomist.py, superuser.py, admin.py
  api/
    main.py  auth.py (initData)  routes/
  webapp/              # index.html, map.js, style.css (Leaflet)
  worker/
    main.py  jobs/ (photos.py, stats.py, reports.py, broadcast.py, cleanup.py)  schedule.py
  reports/
    templates/ (org_daily.html, region.html, base.css)  charts.py  maps.py  facts.py  llm.py
  ml/
    client.py  local.py  space_app/ (app.py, requirements.txt)  train/ (export_dataset.py, train_cls.py, export_onnx.py)
  scripts/
    seed.py  create_admin.py
  migrations/          # Alembic
  tests/
```

## Расписание (Europe/Minsk)

| Время | Задача |
| --- | --- |
| 06:30 | Генерация заданий на день |
| 07:00 | Рассылка заданий работникам |
| 08:00 | «Требует внимания» агрономам |
| 15:00 | Напоминание о невыполненных точках |
| 17:45 | Пересчёт показателей за день |
| 18:00 | Сводки предприятий (шаблон А) |
| 19:00 | Сводка области (шаблон Б) |
| 23:30 | Задания без фото → `missed` |
| 02:00 | Бэкап БД (pg_dump → S3), очистка старых рабочих копий фото |

## Конфигурация

Все настройки — переменные окружения (см. `.env.example`), класс `core/config.py:Settings`.
Переход MinIO → Cloudflare R2 и local → Space для нейросети — только изменением `.env`.
