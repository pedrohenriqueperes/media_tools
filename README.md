# MediaTools

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

Acesse em `http://localhost:8000`.

## Estrutura

```
config/              # Configurações Django (settings, urls, wsgi, celery)
  seo_views.py       # Views para robots.txt e sitemap.xml
core/                # App principal
  models.py          # MediaJob — registro de cada processamento
  tasks.py           # Lógica de processamento de todos os tipos de job
  views.py           # dashboard, submit_job, submit_batch, job_detail
  forms.py           # MediaJobForm com validação por tipo
  urls.py            # Rotas do app
templates/
  base.html          # Navbar flutuante glass pill + design system
  core/              # home, dashboard, submit, submit_batch, job_detail
  account/           # Overrides allauth (login, signup)
media/               # Uploads e outputs (não versionado)
  uploads/           # Arquivos enviados pelo usuário
    batch_{pk}/      # Inputs de jobs de conversão em lote
  outputs/           # Resultados processados
conversor_gif.py     # Script standalone de conversão para GIF
resize_photos.py     # Script standalone de redimensionamento de imagens
resize_videos.py     # Script standalone de compressão de vídeos
frames.py            # Script standalone de extração de frames
image_converter_core.md  # Documentação da lógica de conversão em lote
```

## Rotas principais

| Rota | Descrição |
|---|---|
| `/` | Home pública com descrição das funcionalidades |
| `/dashboard/` | Lista de jobs do usuário (requer login) |
| `/submit/` | Envio de arquivo único para processamento |
| `/submit/batch/` | Envio de múltiplas imagens para conversão em lote |
| `/job/<pk>/` | Detalhes e resultado de um job |
| `/accounts/login/` | Login por e-mail |
| `/accounts/signup/` | Cadastro |
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
python manage.py collectstatic         # para produção
```
