import os
import threading
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # RUN_MAIN=true só existe no processo worker do dev server.
        # Sem essa guarda, a thread seria iniciada duas vezes (reloader + worker).
        if os.environ.get('RUN_MAIN') != 'true':
            return
        from .tasks import cleanup_worker_loop
        t = threading.Thread(target=cleanup_worker_loop, name='cleanup-worker', daemon=True)
        t.start()
