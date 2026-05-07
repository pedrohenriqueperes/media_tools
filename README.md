# MediaTools

**PT** · [EN](#mediatools-1)

Aplicação web Django para processamento de mídia. Faça upload de imagens ou vídeos e execute operações como redimensionamento, compressão, extração de frames, conversão de formato e geração de GIFs — tudo pelo navegador. Os arquivos são apagados automaticamente 60 segundos após o processamento.

## Funcionalidades

| Operação | Entrada | Saída | Detalhes |
|---|---|---|---|
| **Redução de imagem** | JPG, PNG, WEBP, BMP, TIFF | JPEG | Reduz para máx. 800px, qualidade 85 (Pillow) |
| **Compressão de vídeo** | MP4, MOV, AVI, MKV | MP4 | H.264 CRF 23 via ffmpeg |
| **Extração de frames** | MP4, MOV, AVI, MKV | ZIP de JPEGs | OpenCV, todos os frames |
| **Converter formato** | JPG, PNG, WEBP, BMP, TIFF, GIF | JPEG/PNG/WEBP/BMP/TIFF/GIF | Pillow, qualidade otimizada por formato |
| **Imagem para GIF** | JPG, PNG, WEBP, BMP, TIFF | GIF | Pillow |
| **Vídeo para GIF** | MP4, MOV, AVI, MKV | GIF | MoviePy; configurável: fps, início, duração, largura |
| **Conversão em lote** | Até 100 imagens | ZIP | Converte todas para um formato alvo de uma vez |

## Requisitos

- Python 3.11+
- PostgreSQL
- ffmpeg (`brew install ffmpeg`)
- Redis (para Celery)

## Setup

```bash
git clone https://github.com/pedrohenriqueperes/media_tools.git
cd media_tools

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz:

```env
SECRET_KEY=sua-chave-secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=resize_db
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Em outro terminal, inicie o worker Celery (necessário para a limpeza automática de arquivos):

```bash
celery -A config worker -l info
```

Acesse em `http://localhost:8000`.

## Limpeza automática

Os arquivos de input e output são apagados automaticamente **60 segundos** após o término do processamento (sucesso ou erro). O histórico de jobs permanece no dashboard, mas o download não estará mais disponível. Para processar novamente, basta reenviar o arquivo.

## Estrutura

```
config/              # Configurações Django (settings, urls, wsgi, celery)
  seo_views.py       # Views para robots.txt e sitemap.xml
core/                # App principal
  models.py          # MediaJob — registro de cada processamento
  tasks.py           # Lógica de processamento e task de limpeza (Celery)
  views.py           # dashboard, submit_job, submit_batch, job_detail
  forms.py           # MediaJobForm com validação por tipo
templates/
  base.html          # Navbar flutuante + design system CSS
  core/              # home, dashboard, submit, submit_batch, job_detail
  account/           # Overrides allauth (login, signup)
media/               # Uploads e outputs (não versionado)
  uploads/           # Arquivos enviados (input_file dos jobs)
    batch_{pk}/      # Inputs de jobs de conversão em lote
  outputs/{pk}/      # Resultados processados por job
```

## Rotas principais

| Rota | Descrição |
|---|---|
| `/` | Home pública |
| `/dashboard/` | Lista de jobs (requer login) |
| `/submit/` | Envio de arquivo único |
| `/submit/batch/` | Envio de múltiplas imagens para conversão em lote |
| `/job/<pk>/` | Detalhes e resultado de um job |
| `/sitemap.xml` | Sitemap XML |
| `/robots.txt` | Robots.txt |

## Stack

| Camada | Tecnologia |
|---|---|
| Framework | Django 6 |
| Banco de dados | PostgreSQL + psycopg2 |
| Auth | django-allauth (e-mail only) |
| Frontend | Bootstrap 5 + Plus Jakarta Sans + Remix Icons |
| Imagens | Pillow + OpenCV |
| Vídeos | ffmpeg + MoviePy |
| Fila de tarefas | Celery + Redis |
| Static files | Whitenoise |

## Comandos úteis

```bash
python manage.py makemigrations core   # após alterar models.py
python manage.py migrate
python manage.py cleanup_old_jobs      # remove jobs e arquivos com mais de 7 dias
python manage.py cleanup_old_jobs --days 1
```

---

# MediaTools

**EN** · [PT](#mediatools)

A Django web app for media processing. Upload images or videos and run operations like resizing, compression, frame extraction, format conversion and GIF generation — all from the browser. Files are automatically deleted 60 seconds after processing.

## Features

| Operation | Input | Output | Details |
|---|---|---|---|
| **Image resize** | JPG, PNG, WEBP, BMP, TIFF | JPEG | Scales down to max 800px, quality 85 (Pillow) |
| **Video compression** | MP4, MOV, AVI, MKV | MP4 | H.264 CRF 23 via ffmpeg |
| **Frame extraction** | MP4, MOV, AVI, MKV | ZIP of JPEGs | OpenCV, all frames |
| **Format conversion** | JPG, PNG, WEBP, BMP, TIFF, GIF | JPEG/PNG/WEBP/BMP/TIFF/GIF | Pillow, quality optimised per format |
| **Image to GIF** | JPG, PNG, WEBP, BMP, TIFF | GIF | Pillow |
| **Video to GIF** | MP4, MOV, AVI, MKV | GIF | MoviePy; configurable: fps, start, duration, width |
| **Batch conversion** | Up to 100 images | ZIP | Converts all images to a chosen format at once |

## Requirements

- Python 3.11+
- PostgreSQL
- ffmpeg (`brew install ffmpeg`)
- Redis (for Celery)

## Setup

```bash
git clone https://github.com/pedrohenriqueperes/media_tools.git
cd media_tools

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file at the project root:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=resize_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

In a separate terminal, start the Celery worker (required for automatic file cleanup):

```bash
celery -A config worker -l info
```

Open `http://localhost:8000`.

## Automatic cleanup

Input and output files are automatically deleted **60 seconds** after processing completes (success or error). Job history remains visible in the dashboard, but the download link will no longer be available. To process again, simply re-upload the file.

## Project structure

```
config/              # Django project (settings, urls, wsgi, celery)
  seo_views.py       # robots.txt and sitemap.xml views
core/                # Main app
  models.py          # MediaJob — tracks each processing request
  tasks.py           # Processing logic and Celery cleanup task
  views.py           # dashboard, submit_job, submit_batch, job_detail
  forms.py           # MediaJobForm with per-type file validation
templates/
  base.html          # Floating navbar + shared CSS design system
  core/              # home, dashboard, submit, submit_batch, job_detail
  account/           # allauth overrides (login, signup)
media/               # Uploads and outputs (not committed)
  uploads/           # Single-file job inputs (Django FileField)
    batch_{pk}/      # Batch job inputs (saved manually by view)
  outputs/{pk}/      # Processed results, one directory per job
```

## Routes

| Route | Description |
|---|---|
| `/` | Public home page |
| `/dashboard/` | Job list (login required) |
| `/submit/` | Single file upload |
| `/submit/batch/` | Multi-image batch conversion |
| `/job/<pk>/` | Job detail and result download |
| `/sitemap.xml` | XML sitemap |
| `/robots.txt` | Robots.txt |

## Stack

| Layer | Technology |
|---|---|
| Framework | Django 6 |
| Database | PostgreSQL + psycopg2 |
| Auth | django-allauth (email only) |
| Frontend | Bootstrap 5 + Plus Jakarta Sans + Remix Icons |
| Images | Pillow + OpenCV |
| Videos | ffmpeg + MoviePy |
| Task queue | Celery + Redis |
| Static files | Whitenoise |

## Useful commands

```bash
python manage.py makemigrations core       # after changing models.py
python manage.py migrate
python manage.py cleanup_old_jobs          # remove jobs and files older than 7 days
python manage.py cleanup_old_jobs --days 1
```
