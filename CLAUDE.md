# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django web app for media processing (frame extraction, image/video resizing). Uses PostgreSQL, django-allauth for auth, Bootstrap 5 for the frontend.

## Setup

```bash
# Requires: ffmpeg (brew install ffmpeg) and PostgreSQL running locally
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Sensitive config lives in `.env` (not committed). Copy structure from the `.env` section below if starting fresh:
```
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=resize_db
DB_USER=php
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
```

## Architecture

```
config/          # Django project (settings, urls, wsgi)
core/            # Main app
  models.py      # MediaJob — tracks each processing request per user
  tasks.py       # Synchronous processing logic (frames, resize image/video)
  views.py       # dashboard, submit_job, job_detail (all login_required)
  forms.py       # MediaJobForm
templates/
  base.html      # Bootstrap 5 navbar + messages layout
  core/          # dashboard, submit, job_detail
  account/       # allauth login/signup overrides
media/           # Uploaded files and processed outputs (not committed)
```

**Processing flow:** user uploads a file → `MediaJob` record created → `tasks.process_job()` runs synchronously in the same request → job status updated to `done` or `error`. There is no task queue (Celery etc.) yet; large files will block the request.

**Auth:** django-allauth with email-only login (`ACCOUNT_LOGIN_METHODS = {'email'}`). No email verification (`ACCOUNT_EMAIL_VERIFICATION = 'none'`).

## Key commands

```bash
python manage.py makemigrations core   # after changing core/models.py
python manage.py createsuperuser       # admin user
python manage.py collectstatic         # production static files (whitenoise)
```

## Scripts kept from original project

The original standalone scripts are still present at the root and reused inside `core/tasks.py`:
- `resize_photos.py` — Pillow-based image resize (max 800px, JPEG quality 85)
- `resize_videos.py` — ffmpeg h264 CRF 23 compression
- `frames.py` — OpenCV frame extraction (saves as `frame_XXXX.jpg`)
