# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django 6 web app for media processing. Users upload files and choose a job type; processing runs via Celery (Docker/Prod) or daemon threads (local dev). Auth is e-mail only via django-allauth. Frontend uses Bootstrap 5 + Plus Jakarta Sans + Remix Icons with a custom design system defined entirely in `templates/base.html`.

## Setup

### Local Development
```bash
# Prerequisites: ffmpeg (brew install ffmpeg) and PostgreSQL running locally
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Docker Development
```bash
# Build and start containers
docker-compose up -d

# Run migrations and collectstatic (already in docker-compose command, but for manual runs)
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

Sensitive config lives in `.env` (not committed).

## Key commands

```bash
python manage.py makemigrations core   # after changing core/models.py
python manage.py migrate
python manage.py createsuperuser
python manage.py check                 # validate config without running server
```

## Architecture

### Processing flow

1. User submits a file via `submit_job` (single file) or `submit_batch` (multiple files).
2. A `MediaJob` record is created with `status='pending'`.
3. Processing is triggered:
   - **Local Dev**: `process_job_async` spawns a daemon thread calling `process_job()`.
   - **Docker/Prod**: `process_job_task` is queued as a Celery task and processed by the `worker` service.
4. The task sets `status='processing'`, runs the appropriate private function, then saves `status='done'` or `status='error'` in a `finally` block.
5. The job detail page polls `/job/<pk>/status/` every 2.5s and reloads when done.
6. **Cleanup**: `cleanup_old_media` (Celery Beat task) runs every 2 minutes to delete files for jobs completed more than 2 minutes ago.

**Important:** `batch_convert` is the only job type where `input_file` is `None`. All other types access `job.input_file.path` inside the `else` branch of `process_job`. Never move `input_path = job.input_file.path` outside that `else` block.

### Job types and their handlers (core/tasks.py)

| `job_type` | Input | Private fn | Output |
|---|---|---|---|
| `frames` | video | `_extract_frames` + `_zip_dir` | `outputs/{pk}/frames.zip` |
| `resize_image` | image | `_resize_image` | `outputs/{pk}/{name}` |
| `resize_video` | video | `_resize_video` | `outputs/{pk}/{stem}_compressed.mp4` |
| `convert_format` | image | `_convert_image_bytes` | `outputs/{pk}/{stem}.{ext}` |
| `image_to_gif` | image | `_image_to_gif` | `outputs/{pk}/{stem}.gif` |
| `video_to_gif` | video | `_video_to_gif` | `outputs/{pk}/{stem}.gif` |
| `batch_convert` | — | `_batch_convert` | `outputs/{pk}/converted.zip` |

For `batch_convert`, input files are saved by the view to `media/uploads/batch_{pk}/` before the task starts. The task reads from there.

Extra parameters (`fps`, `start`, `duration`, `width` for `video_to_gif`; `target_format` for `convert_format` and `batch_convert`) are stored in `job.job_params` (JSONField).

`frame_count` is repurposed as file count for `batch_convert`.

### Payments

Payments are integrated via an external PIX API (`https://mypayments.store`).
- Logic is implemented in `core/payments.py`.
- **Workflow**: `generate_pix_payment` requests a transaction from the API $\rightarrow$ user is shown the payment page (`templates/core/job_payment.html`) $\rightarrow$ `verify_pix_payment` polls the API to confirm payment.

### Adding a new job type

1. Add the choice to `MediaJob.TYPE_CHOICES` in `core/models.py`.
2. Run `python manage.py makemigrations core`.
3. Add an `elif job.job_type == '...'` branch inside the `else` block of `process_job()` in `core/tasks.py`.
4. Update validation in `core/forms.py` (`clean` method checks file extensions per type).
5. Add `<option>` to the select in `templates/core/submit.html`.
6. Add result rendering in `templates/core/job_detail.html`.
7. Add an icon in `templates/core/dashboard.html` and `job_detail.html`.

### File storage layout

```
media/
  uploads/          # Single-file uploads (Django FileField, upload_to='uploads/')
    batch_{pk}/     # Batch job inputs (saved manually by submit_batch view)
  outputs/{pk}/     # Processed results, one dir per job
```

`output_path` on the model is stored relative to `MEDIA_ROOT` (e.g. `outputs/42/frames.zip`). In views, prepend `settings.MEDIA_URL` to build the URL.

### Template system

All pages extend `templates/base.html`, which defines:
- Floating glass pill navbar (fixed, z-index 200)
- CSS variables (`--c-bg`, `--c-card`, `--c-border`, `--c-accent`, etc.) used across all interior pages
- Global button overrides for `.btn-primary` and `.btn-outline-secondary`
- Status pill classes: `.spill-done`, `.spill-processing`, `.spill-error`, `.spill-pending`
- `{% block meta_robots %}`, `{% block meta_description %}`, `{% block og_title %}`, etc. for per-page SEO
- `{% block footer %}` — overridden to empty in login/signup pages
- `{% block main_class %}` — overridden to empty in `home.html` (full-width dark page)

The home page (`templates/core/home.html`) sets `body_class=page-home` and `main_class` to empty to opt out of the light interior layout.

### Auth

django-allauth with e-mail only login. No e-mail verification. Overridden templates in `templates/account/`. `LOGIN_REDIRECT_URL = '/dashboard/'`, `LOGOUT_REDIRECT_URL = '/'`.

### SEO

- `robots.txt` and `sitemap.xml` served by `config/seo_views.py` (no sitemaps framework — plain Python views).
- Protected pages (`dashboard`, `submit`, `job_detail`) set `{% block meta_robots %}noindex, nofollow{% endblock %}`.
- JSON-LD schema on home page via `{% block structured_data %}`.
