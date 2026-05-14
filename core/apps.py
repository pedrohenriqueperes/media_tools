import os
import threading
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Migrado para Celery Beat para maior confiabilidade em produção
        pass
