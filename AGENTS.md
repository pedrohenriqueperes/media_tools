# AGENTS.md

This file provides context and guidance for any AI coding agent working on this repository.

## Project Overview

**MediaTools** is a Django web application for media processing. Users upload images or videos and run operations like resizing, compression, frame extraction, format conversion, and GIF generation — all from the browser.

### Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 6 (Python 3.12) |
| Database | PostgreSQL + psycopg2 |
| Task Queue | Celery with Redis |
| Auth | django-allauth (email-only login) |
| Frontend | Bootstrap 5 + Plus Jakarta Sans + Remix Icons |
| Images | Pillow + OpenCV |
| Videos | ffmpeg + MoviePy |
| Static Files | Whitenoise |
| Containerization | Docker & Docker Compose |
| Payments | External PIX API (`https://mypayments.store`) |

---

## Setup

### Local Development (preferred for day-to-day)

```bash
# Prerequisites: ffmpeg (brew install ffmpeg), PostgreSQL running locally
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Docker Environment

```bash
docker-compose up --build
```

**Services:** `db` (PostgreSQL 15, host port 5433), `redis` (Redis 7), `web` (Django, port 8000), `worker` (Celery worker), `beat` (Celery beat).

### Environment Variables (`.env`, not committed)

```
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=resize_db
DB_USER=...
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST_USER=...        # Gmail address
EMAIL_HOST_PASSWORD=...    # Gmail App Password
PAYMENT_API_URL=...        # defaults to https://mypayments.store
```

### Key Commands

```bash
python manage.py makemigrations core   # after changing core/models.py
python manage.py migrate
python manage.py createsuperuser
python manage.py check                 # validate config without running server
celery -A config worker -l info        # start Celery worker (local dev)
celery -A config beat -l info          # start Celery beat (local dev)
python manage.py cleanup_old_jobs      # manually remove records older than 7 days
```

---

## Architecture

### Project Structure

```
config/                  # Django project settings
  settings.py            # Main settings (DB, Celery, allauth, email, etc.)
  urls.py                # Root URL conf — includes core.urls and allauth
  celery.py              # Celery app definition
  seo_views.py           # robots.txt and sitemap.xml (plain Python views, no framework)
  wsgi.py / asgi.py
core/                    # Main application
  models.py              # MediaJob (task record) + JobPricing (per-type pricing)
  tasks.py               # All processing logic + cleanup + Celery tasks
  views.py               # dashboard, submit_job, submit_batch, job_detail, payments
  forms.py               # MediaJobForm with per-type file extension validation
  payments.py            # External PIX API integration (generate + verify)
  urls.py                # App URL patterns
  apps.py                # AppConfig (starts cleanup thread on ready)
  admin.py               # Admin registration for MediaJob and JobPricing
  management/            # Management commands (cleanup_old_jobs)
templates/
  base.html              # Floating glass pill navbar + full CSS design system
  core/                  # home, dashboard, submit, submit_batch, job_detail, job_payment
  account/               # allauth overrides (login, signup)
media/                   # Uploads and outputs (not committed)
  uploads/               # Input files
    batch_{pk}/          # Batch conversion inputs (saved manually by view)
  outputs/{pk}/          # Processed results, one directory per job
```

### Processing Flow

1. User submits a file via `submit_job` (single) or `submit_batch` (multiple files).
2. A `MediaJob` record is created with `status='pending'`.
3. If the job type has a configured price > 0, user is redirected to `job_payment` for PIX payment. Processing only starts after payment is confirmed.
4. `process_job_task.delay(job.pk)` dispatches to Celery (or `process_job_async()` runs in a daemon thread in dev).
5. The task sets `status='processing'`, runs the appropriate handler, then saves `status='done'` or `status='error'`.
6. The job detail page polls `/job/<pk>/status/` every 2.5s and reloads when done.

### Job Types and Handlers (`core/tasks.py`)

| `job_type` | Input | Private Handler | Output |
|---|---|---|---|
| `frames` | video | `_extract_frames` + `_zip_dir` | `outputs/{pk}/frames.zip` |
| `resize_image` | image | `_resize_image` | `outputs/{pk}/{name}` |
| `resize_video` | video | `_resize_video` | `outputs/{pk}/{stem}_compressed.mp4` |
| `convert_format` | image | `_convert_image_bytes` | `outputs/{pk}/{stem}.{ext}` |
| `image_to_gif` | image | `_image_to_gif` | `outputs/{pk}/{stem}.gif` |
| `video_to_gif` | video | `_video_to_gif` | `outputs/{pk}/{stem}.gif` |
| `batch_convert` | — | `_batch_convert` | `outputs/{pk}/converted.zip` |

> **Critical:** `batch_convert` is the **only** job type where `input_file` is `None`. All other types access `job.input_file.path` inside the `else` branch of `process_job_task`. Never move `input_path = job.input_file.path` outside that `else` block.

Extra parameters (`fps`, `start`, `duration`, `width` for `video_to_gif`; `target_format` for `convert_format` and `batch_convert`) are stored in `job.job_params` (JSONField). `frame_count` is repurposed as file count for `batch_convert`.

### File Cleanup

- **Automatic:** A Celery Beat task (`cleanup_old_media`) runs every 2 minutes and deletes files from jobs completed more than 2 minutes ago.
- **Dev alternative:** A background thread (`cleanup_worker_loop`) starts with the server via `AppConfig.ready()` and scans every 30 seconds, deleting files 60 seconds after job completion.
- **Manual:** `python manage.py cleanup_old_jobs [--days N]` removes records older than N days (default 7).

### Payment System

- Pricing per job type is configured via Django Admin under **Preços das Tarefas** (`JobPricing` model).
- Tasks with `price > 0` set `payment_status='pending'` and redirect to `job_payment` view.
- The payment page shows a PIX QR code and polls `/job/<pk>/check-payment/` until approved.
- On approval, `process_job_task.delay()` is called to start processing.
- PIX integration uses an external API at `PAYMENT_API_URL` (see `core/payments.py`).

---

## Adding a New Job Type

1. Add the choice to `MediaJob.TYPE_CHOICES` in `core/models.py`.
2. Run `python manage.py makemigrations core && python manage.py migrate`.
3. Add an `elif job.job_type == '...'` branch inside the `else` block of `process_job_task()` in `core/tasks.py`.
4. Update validation in `core/forms.py` (`clean()` checks file extensions per type).
5. Add `<option>` to the select in `templates/core/submit.html`.
6. Add result rendering in `templates/core/job_detail.html`.
7. Add an icon in `templates/core/dashboard.html` and `job_detail.html`.

---

## Template System

All pages extend `templates/base.html`, which defines:

- **Navbar:** Floating glass pill navbar (fixed, z-index 200)
- **CSS Variables:** `--c-bg`, `--c-card`, `--c-border`, `--c-accent`, etc.
- **Button overrides:** `.btn-primary` and `.btn-outline-secondary`
- **Status pills:** `.spill-done`, `.spill-processing`, `.spill-error`, `.spill-pending`
- **SEO blocks:** `{% block meta_robots %}`, `{% block meta_description %}`, `{% block og_title %}`, etc.
- **Layout blocks:** `{% block footer %}` (overridden to empty in login/signup), `{% block main_class %}` (overridden to empty in `home.html` for full-width dark layout)

The home page (`templates/core/home.html`) sets `body_class=page-home` and empties `main_class` to opt out of the light interior layout.

---

## Auth

- **Provider:** django-allauth with email-only login (no username).
- **Email verification:** `mandatory` (configurable in `settings.py`).
- **Redirects:** `LOGIN_REDIRECT_URL = '/dashboard/'`, `LOGOUT_REDIRECT_URL = '/'`.
- **Templates:** Overridden in `templates/account/`.
- **Sites framework:** `SITE_ID=1` — update domain in Django Admin if needed for correct email links.

---

## SEO

- `robots.txt` and `sitemap.xml` served by `config/seo_views.py` (plain Python views, no sitemaps framework).
- Protected pages (`dashboard`, `submit`, `job_detail`) set `{% block meta_robots %}noindex, nofollow{% endblock %}`.
- JSON-LD schema on home page via `{% block structured_data %}`.

---

## URL Routes

| Route | View | Auth | Description |
|---|---|---|---|
| `/` | `home` | No | Public home (redirects to dashboard if logged in) |
| `/dashboard/` | `dashboard` | Yes | Paginated task list |
| `/submit/` | `submit_job` | Yes | Single file upload + processing |
| `/submit/batch/` | `submit_batch` | Yes | Multi-image batch conversion (up to 100) |
| `/job/<pk>/` | `job_detail` | Yes | Task detail and result download |
| `/job/<pk>/status/` | `job_status` | Yes | JSON status polling endpoint |
| `/job/<pk>/payment/` | `job_payment` | Yes | PIX payment page |
| `/job/<pk>/check-payment/` | `check_payment` | Yes | JSON payment status polling |
| `/job/<pk>/delete/` | `delete_job` | Yes | Delete a single job (POST) |
| `/jobs/clear/` | `clear_jobs` | Yes | Delete all user jobs (POST) |
| `/webhook/` | `payment_webhook` | No | PIX payment status webhook (POST, csrf_exempt) |
| `/sitemap.xml` | — | No | XML sitemap |
| `/robots.txt` | — | No | Robots.txt |

---

## Development Conventions

- **Migrations:** Always run `python manage.py makemigrations core` then `python manage.py migrate` after model changes.
- **Upload limit:** 200 MB (`DATA_UPLOAD_MAX_MEMORY_SIZE` and `FILE_UPLOAD_MAX_MEMORY_SIZE` in settings).
- **File storage:** `output_path` on the model is relative to `MEDIA_ROOT` (e.g., `outputs/42/frames.zip`). Prepend `settings.MEDIA_URL` to build URLs in views.
- **Docker media:** Stored in named volumes; inspect via `docker-compose exec web ls /app/media`.
- **Celery in Docker:** Worker runs with `--concurrency=2` and 4GB memory limit.
- **Language:** UI and code comments are primarily in Portuguese (pt-BR). `LANGUAGE_CODE = 'pt-br'`, `TIME_ZONE = 'America/Sao_Paulo'`.
