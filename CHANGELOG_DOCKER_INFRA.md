# Changelog: Infraestrutura, Docker e Celery

Este documento registra as alterações técnicas realizadas para modernizar a infraestrutura do projeto, habilitar o uso de containers e garantir a estabilidade do processamento de mídias.

## 1. Autenticação e E-mail (Django-Allauth)
- **Servidor SMTP:** Configurado para utilizar o Gmail como gateway de envio.
- **Segurança:** Implementado uso de TLS na porta 587.
- **Verificação de E-mail:** Alterada de `none` para `mandatory`. O usuário agora precisa confirmar o e-mail para acessar o dashboard.
- **UX:** Ativado `ACCOUNT_CONFIRM_EMAIL_ON_GET` para permitir confirmação de conta com apenas um clique no link recebido.

## 2. Dockerização Completa
- **Dockerfile:** Criado utilizando a imagem base `python:3.12-slim`. Inclui dependências de sistema para processamento de vídeo e imagem (`ffmpeg`, `libsm6`, `libxext6`).
- **Orquestração (Docker Compose):** Implementados 5 serviços:
  - `web`: Aplicação Django principal.
  - `db`: PostgreSQL 15 (Porta externa 5433 para evitar conflitos locais).
  - `redis`: Redis 7 como broker de mensagens.
  - `worker`: Processamento assíncrono do Celery.
  - `beat`: Agendador de tarefas periódicas do Celery.
- **Volumes:** Criados volumes nomeados para persistência do banco de dados e arquivos de mídia.

## 3. Estabilidade e Performance (Celery)
- **Migração de Threads para Tasks:** O processamento de vídeos e imagens foi movido de threads locais para tarefas reais do Celery (`process_job_task`). Isso impede que o servidor web trave ou caia durante conversões pesadas.
- **Otimização de Recursos:**
  - Limite de memória do Worker aumentado para **4GB** no Docker Compose.
  - Concorrência do Worker limitada a **2 processos simultâneos** para evitar exaustão de CPU/RAM (OOM).
- **Limpeza Automática:** Implementada a tarefa `cleanup_old_media` via **Celery Beat**. 
  - Frequência: A cada 2 minutos.
  - Regra: Remove arquivos de jobs concluídos há mais de 2 minutos.

## 4. Ajustes de Ambiente
- **Configuração via .env:** Todas as chaves sensíveis e endereços de rede (DB_HOST, CELERY_BROKER_URL) foram centralizadas no `.env`.
- **Acesso:** Adicionado `0.0.0.0` ao `ALLOWED_HOSTS` para permitir o acesso correto via container.

---
*Data das alterações: 13 de Maio de 2026*
