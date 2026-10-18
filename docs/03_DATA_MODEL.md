# 03. Модель данных

PostgreSQL 16 + PostGIS. Время — `timestamptz` (UTC). Координаты — `geography(Point, 4326)`, границы — `geography(Polygon, 4326)`.
Первичные ключи — `bigint identity` (кроме `invites.code`). Фото в БД не храним — только ссылки.

## Перечисления

- `user_role`: worker, agronomist, superuser, admin
- `point_kind`: regular, risk, focus
- `task_status`: pending, done, missed
- `photo_kind`: overview, plant, closeup, underside
- `verdict`: healthy, suspect, disease, reshoot
- `focus_status`: active, treated, closed
- `trend`: up, flat, down

## Таблицы

### Территория и пользователи
- **regions**(id, name)
- **districts**(id, region_id → regions, name)
- **organizations**(id, name, district_id → districts, location Point, created_at)
- **users**(id, tg_id bigint unique, full_name, role user_role, org_id → organizations null, region_id → regions null, is_active bool, consent_at, created_at)
  - worker/agronomist: org_id NOT NULL; superuser: region_id NOT NULL (CHECK).
- **invites**(code text pk, role, org_id null, region_id null, created_by → users, expires_at, used_by → users null, used_at null)

### Справочники
- **crops**(id, name, is_active)
- **diseases**(id, crop_id → crops, name, latin_name, severity_scale jsonb, reference_photo_keys text[], is_active)
  - `severity_scale` пример: `{"max": 4, "labels": {"0": "нет", "1": "слабое", "2": "среднее", "3": "сильное", "4": "очень сильное"}}`

### Поля и сбор данных
- **fields**(id, org_id → organizations, name, crop_id → crops, area_ha numeric, boundary Polygon null, centroid Point, growth_stage text null, daily_mode bool default false, is_active)
- **control_points**(id, field_id → fields, location Point, kind point_kind, assigned_user_id → users null, interval_days int default 3, is_active, created_at)
- **tasks**(id, point_id → control_points, user_id → users, date date, status task_status, done_at null) — unique(point_id, date)
- **observations**(id, task_id → tasks null, point_id → control_points null, user_id → users, location Point, distance_m numeric null, taken_at, plants_inspected int default 10, plants_affected int, wet_leaves bool, is_unplanned bool, comment text null)
- **photos**(id, observation_id → observations, kind photo_kind, s3_key text null, tg_file_id text, tg_file_unique_id text, archive_msg_id bigint null, width int, height int, blur_score float, brightness float, quality_ok bool, keep_forever bool default false, created_at)

### Разметка, очаги, обработки
- **ai_predictions**(id, photo_id → photos, model_version text, top1_disease_id → diseases null, top1_label text, top1_prob float, top3 jsonb, created_at)
- **assessments**(id, observation_id → observations, agronomist_id → users, verdict, disease_id → diseases null, severity int null, confirmed_on_site bool default false, comment text null, created_at)
  - Последняя запись по observation — действующая. При verdict in (suspect, disease) → `photos.keep_forever = true`.
- **foci**(id, field_id → fields, disease_id → diseases, point_id → control_points null, location Point, area_ha numeric null, status focus_status, detected_at, closed_at null, created_by → users)
- **focus_updates**(id, focus_id → foci, date, prevalence_pct numeric, severity numeric null, note text null)
- **treatments**(id, field_id → fields, focus_id → foci null, date, product text, rate text, area_ha numeric, created_by → users)

### Коммуникации и аналитика
- **messages**(id, from_user → users, to_user → users null, scope text null /* 'region:5' | 'district:12' | 'org:3' */, ref_type text null, ref_id bigint null, text, sent_at)
- **daily_field_stats**(field_id, date, prevalence_pct numeric null, severity_avg numeric null, speed_pp_day numeric null, trend trend null, n_observations int, last_photo_at null) — pk(field_id, date)
- **daily_user_stats**(user_id, date, tasks_total, tasks_done, photos, photos_ok, avg_distance_m numeric null, unplanned int) — pk(user_id, date)
- **reports**(id, scope text /* org|region */, scope_id bigint, period_from date, period_to date, s3_key text, facts jsonb, llm_summary jsonb null, facts_hash text, created_at)

## Индексы
- GIST: organizations.location, fields.boundary, fields.centroid, control_points.location, observations.location, foci.location.
- B-tree: tasks(user_id, date), tasks(date, status), observations(point_id, taken_at), photos(observation_id), assessments(observation_id, created_at desc), foci(field_id, status), users(tg_id).

## Ключевые запросы

Расстояние до точки (метры):
```sql
SELECT ST_Distance(location, ST_MakePoint(:lon, :lat)::geography) FROM control_points WHERE id = :point_id;
```

Распространённость по полю за 3 дня:
```sql
SELECT cp.field_id,
       100.0 * SUM(o.plants_affected) / NULLIF(SUM(o.plants_inspected), 0) AS prevalence_pct,
       COUNT(*) AS n_observations, MAX(o.taken_at) AS last_photo_at
FROM observations o JOIN control_points cp ON cp.id = o.point_id
WHERE o.taken_at >= :day - INTERVAL '3 days' AND o.taken_at < :day + INTERVAL '1 day'
GROUP BY cp.field_id;
```

## Seed (scripts/seed.py)
1 область, 2 района, 2 предприятия, по 3 поля (картофель, озимая пшеница, рапс), по 5 точек;
культуры и болезни: картофель — фитофтороз, альтернариоз; пшеница — септориоз, бурая ржавчина, мучнистая роса, фузариоз;
рапс — склеротиниоз, альтернариоз. Коды-приглашения для каждой роли печатаются в консоль.
