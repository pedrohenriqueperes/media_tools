# Resize

Aplicação web Django para processamento de mídia. Faça upload de imagens ou vídeos e execute operações como extração de frames, redimensionamento de imagens e compressão de vídeos — tudo pelo navegador.

## Funcionalidades

- **Extração de frames** — extrai frames de vídeos e salva como JPEG via OpenCV
- **Redimensionamento de imagem** — reduz para no máximo 800px mantendo proporção, JPEG qualidade 85 (Pillow)
- **Compressão de vídeo** — reencoda em H.264 CRF 23 com ffmpeg
- **Autenticação** — login por e-mail via django-allauth
- **Dashboard** — histórico de jobs com status, tamanho original/final e percentual de redução

## Requisitos

- Python 3.11+
- PostgreSQL
- ffmpeg (`brew install ffmpeg`)
- Redis (para Celery)

## Setup

```bash
git clone <repo>
cd resize

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
config/          # Configurações Django (settings, urls, wsgi, celery)
core/            # App principal
  models.py      # MediaJob — registro de cada processamento
  tasks.py       # Lógica de processamento (frames, resize imagem/vídeo)
  views.py       # dashboard, submit_job, job_detail
  forms.py       # MediaJobForm
templates/
  base.html      # Layout Bootstrap 5
  core/          # dashboard, submit, job_detail
  account/       # Overrides allauth
media/           # Uploads e outputs (não versionado)
frames.py        # Script standalone de extração de frames
resize_photos.py # Script standalone de redimensionamento de imagens
resize_videos.py # Script standalone de compressão de vídeos
```

## Stack

| Camada | Tecnologia |
|---|---|
| Framework | Django 6 |
| Banco de dados | PostgreSQL + psycopg2 |
| Auth | django-allauth |
| Frontend | Bootstrap 5 |
| Imagens | Pillow + OpenCV |
| Vídeos | ffmpeg + MoviePy |
| Fila de tarefas | Celery + Redis |
| Static files | Whitenoise |

## Comandos úteis

```bash
python manage.py makemigrations core   # após alterar models.py
python manage.py collectstatic         # para produção
```
# media_tools
