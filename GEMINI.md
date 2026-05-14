# Project Overview

This project is a Django-based web application for converting images and videos to GIF format. It supports various image manipulations, batch conversions, and uses Celery for asynchronous processing.

## Tech Stack

- **Backend:** Django (Python 3.12)
- **Database:** PostgreSQL
- **Task Queue:** Celery with Redis
- **Containerization:** Docker & Docker Compose
- **Email:** Django-allauth with Gmail SMTP
- **Payments:** External PIX API (`https://mypayments.store`)
- **Processing Libraries:** Pillow, MoviePy, OpenCV

## Docker Environment

The project is fully containerized. To run the environment:

```bash
docker-compose up --build
```

### Services:
- `db`: PostgreSQL 15 (mapped to host port 5433)
- `redis`: Redis 7 (Celery Broker)
- `web`: Django application (port 8000)
- `worker`: Celery worker for image/video processing
- `beat`: Celery beat for scheduled tasks (e.g., media cleanup)

## Configuration

Environment variables are managed via a `.env` file.

### Email Setup (Gmail)
- `EMAIL_HOST_USER`: Your Gmail address
- `EMAIL_HOST_PASSWORD`: Gmail App Password
- Email verification is set to `mandatory`.

### Media Cleanup
Files are automatically deleted by a Celery Beat task (`cleanup_old_media`) every 2 minutes. Files older than 2 minutes after job completion are removed.

### Payment System
Pricing for each task type is configurable via the Django Admin under **Preços das Tarefas**. 
- Tasks with price > 0.00 will block processing until PIX payment is confirmed.
- Automatic polling on the payment page releases the task to Celery upon approval.

## Local Development (Non-Docker)

While Docker is preferred, you can run locally:

1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` with local DB/Redis paths.
3. Run migrations: `python manage.py migrate`
4. Start worker: `celery -A config worker -l info`
5. Start beat: `celery -A config beat -l info`
6. Start server: `python manage.py runserver`

## Development Conventions

- **Migrations:** Always run `python manage.py migrate` after adding new apps or changing models.
- **Sites Framework:** Uses `django.contrib.sites` (SITE_ID=1). Remember to update the domain in Django Admin if needed for correct email links.
- **Media:** Stored in named volumes in Docker for persistence, but can be explored via `docker-compose exec web ls /app/media`.
