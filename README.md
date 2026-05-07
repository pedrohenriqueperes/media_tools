# MediaTools

**PT** · [EN](#mediatools-1)

Aplicação web Django para processamento de mídia. Faça upload de imagens ou vídeos e execute operações como redimensionamento, compressão, extração de frames, conversão de formato e geração de GIFs — tudo pelo navegador.

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

Acesse em `http://localhost:8000`.

## Limpeza automática de arquivos

Os arquivos de input e output são **apagados automaticamente 60 segundos** após o término do processamento, tanto para tarefas concluídas quanto para erros. Nenhuma configuração extra é necessária — uma thread de background inicia junto com o servidor e escaneia o banco a cada 30 segundos.

O histórico de tarefas permanece visível no dashboard. Após a expiração, o download não estará mais disponível e a interface exibe um aviso. Para processar novamente, basta reenviar o arquivo.

Para remover tarefas e arquivos mais antigos manualmente:

```bash
python manage.py cleanup_old_jobs           # padrão: remove registros com mais de 7 dias
python manage.py cleanup_old_jobs --days 1
```

## Estrutura

```
config/              # Configurações Django (settings, urls, wsgi, celery)
  seo_views.py       # Views para robots.txt e sitemap.xml
core/
  models.py          # MediaJob — registro de cada tarefa
  tasks.py           # Lógica de processamento + cleanup_worker_loop
  apps.py            # Inicia a thread de limpeza no AppConfig.ready()
  views.py           # dashboard, submit_job, submit_batch, job_detail
  forms.py           # MediaJobForm com validação por tipo
templates/
  base.html          # Navbar flutuante + design system CSS
  core/              # home, dashboard, submit, submit_batch, job_detail
  account/           # Overrides allauth (login, signup)
media/               # Uploads e outputs (não versionado)
  uploads/           # Arquivos de input (tarefas únicas e lote)
    batch_{pk}/      # Inputs de conversão em lote
  outputs/{pk}/      # Resultados processados, um diretório por tarefa
```

## Rotas principais

| Rota | Descrição |
|---|---|
| `/` | Home pública |
| `/dashboard/` | Lista de tarefas (requer login) |
| `/submit/` | Nova tarefa — arquivo único |
| `/submit/batch/` | Conversão em lote de imagens |
| `/job/<pk>/` | Detalhe e download do resultado |
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
| Static files | Whitenoise |

---

# MediaTools

**EN** · [PT](#mediatools)

A Django web app for media processing. Upload images or videos and run operations like resizing, compression, frame extraction, format conversion and GIF generation — all from the browser.

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

Open `http://localhost:8000`.

## Automatic file cleanup

Input and output files are **automatically deleted 60 seconds** after processing completes, for both successful and failed tasks. No extra configuration required — a background thread starts with the server and scans the database every 30 seconds.

Task history remains visible in the dashboard. After expiry, the download is no longer available and the UI shows a notice. To process again, simply re-upload the file.

To manually remove old tasks and files:

```bash
python manage.py cleanup_old_jobs           # default: removes records older than 7 days
python manage.py cleanup_old_jobs --days 1
```

## Project structure

```
config/              # Django project (settings, urls, wsgi, celery)
  seo_views.py       # robots.txt and sitemap.xml views
core/
  models.py          # MediaJob — tracks each task
  tasks.py           # Processing logic + cleanup_worker_loop
  apps.py            # Starts the cleanup thread in AppConfig.ready()
  views.py           # dashboard, submit_job, submit_batch, job_detail
  forms.py           # MediaJobForm with per-type file validation
templates/
  base.html          # Floating navbar + shared CSS design system
  core/              # home, dashboard, submit, submit_batch, job_detail
  account/           # allauth overrides (login, signup)
media/               # Uploads and outputs (not committed)
  uploads/           # Input files (single tasks and batch)
    batch_{pk}/      # Batch conversion inputs
  outputs/{pk}/      # Processed results, one directory per task
```

## Routes

| Route | Description |
|---|---|
| `/` | Public home page |
| `/dashboard/` | Task list (login required) |
| `/submit/` | New task — single file |
| `/submit/batch/` | Multi-image batch conversion |
| `/job/<pk>/` | Task detail and result download |
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
| Static files | Whitenoise |
