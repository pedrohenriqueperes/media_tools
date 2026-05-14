# MediaTools

**PT** · [EN](#mediatools-1)

Aplicação web Django para processamento de mídia. Faça upload de imagens ou vídeos e execute operações como redimensionamento, compressão, extração de frames, conversão de formato e geração de GIFs — tudo pelo navegador. Suporte a pagamentos PIX para tarefas pagas.

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

- Python 3.12+
- PostgreSQL
- Redis
- ffmpeg (`brew install ffmpeg`) — apenas para dev local

## Setup — Dev Local

```bash
git clone https://github.com/pedrohenriqueperes/media_tools.git
cd media_tools

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz (use `.env.example` como base):

```env
SECRET_KEY=sua-chave-secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=resize_db
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
CELERY_BROKER_URL=redis://localhost:6379/0
PAYMENT_API_URL=https://mypayments.store
EMAIL_HOST_USER=seu@gmail.com
EMAIL_HOST_PASSWORD=sua-app-password
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse em `http://localhost:8000`.

## Setup — Docker

```bash
cp .env.example .env   # preencha as variáveis
docker-compose up --build
```

O `docker-compose.yml` sobe 5 serviços:

| Serviço | Papel |
|---|---|
| `db` | PostgreSQL 15 |
| `redis` | Broker Celery |
| `web` | Django (runserver na porta 8000) |
| `worker` | Celery worker (concurrency=2, limite 4 GB RAM) |
| `beat` | Celery Beat — limpeza automática a cada 2 min |

Migrações e `collectstatic` rodam automaticamente no startup do `web`.

## Pagamentos PIX

Tarefas podem ter preço configurado via admin (`JobPricing`). Se o preço for `> 0`, o usuário é redirecionado para uma página de pagamento PIX antes do processamento.

**Fluxo:**
1. Usuário submete a tarefa → view verifica preço em `JobPricing`
2. Se pago: gera cobrança na API externa (`PAYMENT_API_URL`) → exibe QR Code e chave Copia e Cola
3. Página de pagamento faz polling em `/job/<pk>/check-payment/` a cada 3s
4. Após confirmação → processamento inicia normalmente

A API de pagamentos é configurada via `PAYMENT_API_URL` no `.env`. Sem configuração de preço, tarefas ficam gratuitas (`payment_status = 'free'`).

## Limpeza automática de arquivos

Os arquivos de input e output são **apagados automaticamente** após o término do processamento:

- **Local**: thread de background inicia junto com o servidor (`AppConfig.ready()`), escaneia o banco a cada 30s e apaga arquivos de tarefas concluídas há mais de 60s.
- **Docker/Prod**: Celery Beat executa `cleanup_old_media` a cada 2 minutos.

O histórico de tarefas permanece visível no dashboard. Após a expiração, o download não estará mais disponível e a interface exibe um aviso.

## Estrutura

```
config/              # Configurações Django (settings, urls, wsgi, celery)
  seo_views.py       # Views para robots.txt e sitemap.xml
core/
  models.py          # MediaJob + JobPricing
  tasks.py           # Lógica de processamento + cleanup_old_media + cleanup_worker_loop
  payments.py        # generate_pix_payment / verify_pix_payment (API externa)
  apps.py            # Inicia a thread de limpeza no AppConfig.ready()
  views.py           # dashboard, submit_job, submit_batch, job_detail, job_payment
  forms.py           # MediaJobForm com validação por tipo
templates/
  base.html          # Navbar flutuante + design system CSS
  core/              # home, dashboard, submit, submit_batch, job_detail, job_payment
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
| `/job/<pk>/payment/` | Página de pagamento PIX |
| `/job/<pk>/check-payment/` | Polling do status do pagamento |
| `/webhook/` | Webhook de confirmação de pagamento |
| `/sitemap.xml` | Sitemap XML |
| `/robots.txt` | Robots.txt |

## Stack

| Camada | Tecnologia |
|---|---|
| Framework | Django 6 |
| Banco de dados | PostgreSQL + psycopg2 |
| Fila de tarefas | Celery + Redis |
| Auth | django-allauth (e-mail only, verificação obrigatória) |
| Frontend | Bootstrap 5 + Plus Jakarta Sans + Remix Icons |
| Imagens | Pillow + OpenCV |
| Vídeos | ffmpeg + MoviePy |
| Pagamentos | PIX via API externa (`mypayments.store`) |
| Static files | Whitenoise |
| Containerização | Docker + Docker Compose |

---

# MediaTools

**EN** · [PT](#mediatools)

A Django web app for media processing. Upload images or videos and run operations like resizing, compression, frame extraction, format conversion and GIF generation — all from the browser. PIX payment support for paid tasks.

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

- Python 3.12+
- PostgreSQL
- Redis
- ffmpeg (`brew install ffmpeg`) — local dev only

## Setup — Local Dev

```bash
git clone https://github.com/pedrohenriqueperes/media_tools.git
cd media_tools

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file at the project root (use `.env.example` as a template):

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=resize_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
CELERY_BROKER_URL=redis://localhost:6379/0
PAYMENT_API_URL=https://mypayments.store
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://localhost:8000`.

## Setup — Docker

```bash
cp .env.example .env   # fill in variables
docker-compose up --build
```

`docker-compose.yml` brings up 5 services:

| Service | Role |
|---|---|
| `db` | PostgreSQL 15 |
| `redis` | Celery broker |
| `web` | Django (runserver on port 8000) |
| `worker` | Celery worker (concurrency=2, 4 GB RAM limit) |
| `beat` | Celery Beat — automatic cleanup every 2 min |

Migrations and `collectstatic` run automatically on `web` startup.

## PIX Payments

Tasks can have a price configured via the admin panel (`JobPricing`). If the price is `> 0`, the user is redirected to a PIX payment page before processing starts.

**Flow:**
1. User submits a task → view checks price in `JobPricing`
2. If paid: generates a charge on the external API (`PAYMENT_API_URL`) → displays QR Code and Pix copy-paste key
3. Payment page polls `/job/<pk>/check-payment/` every 3s
4. After confirmation → processing starts normally

The payment API is configured via `PAYMENT_API_URL` in `.env`. Without a configured price, tasks remain free (`payment_status = 'free'`).

## Automatic file cleanup

Input and output files are **automatically deleted** after processing completes:

- **Local**: a background thread starts with the server (`AppConfig.ready()`), scans the database every 30s, and deletes files for tasks completed more than 60s ago.
- **Docker/Prod**: Celery Beat runs `cleanup_old_media` every 2 minutes.

Task history stays visible in the dashboard. After expiry, the download is no longer available and the UI shows a notice.

## Project structure

```
config/              # Django project (settings, urls, wsgi, celery)
  seo_views.py       # robots.txt and sitemap.xml views
core/
  models.py          # MediaJob + JobPricing
  tasks.py           # Processing logic + cleanup_old_media + cleanup_worker_loop
  payments.py        # generate_pix_payment / verify_pix_payment (external API)
  apps.py            # Starts the cleanup thread in AppConfig.ready()
  views.py           # dashboard, submit_job, submit_batch, job_detail, job_payment
  forms.py           # MediaJobForm with per-type file validation
templates/
  base.html          # Floating navbar + shared CSS design system
  core/              # home, dashboard, submit, submit_batch, job_detail, job_payment
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
| `/job/<pk>/payment/` | PIX payment page |
| `/job/<pk>/check-payment/` | Payment status polling |
| `/webhook/` | Payment confirmation webhook |
| `/sitemap.xml` | XML sitemap |
| `/robots.txt` | Robots.txt |

## Stack

| Layer | Technology |
|---|---|
| Framework | Django 6 |
| Database | PostgreSQL + psycopg2 |
| Task queue | Celery + Redis |
| Auth | django-allauth (email only, mandatory verification) |
| Frontend | Bootstrap 5 + Plus Jakarta Sans + Remix Icons |
| Images | Pillow + OpenCV |
| Videos | ffmpeg + MoviePy |
| Payments | PIX via external API (`mypayments.store`) |
| Static files | Whitenoise |
| Containerisation | Docker + Docker Compose |
