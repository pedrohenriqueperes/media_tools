from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import MediaJob


class Command(BaseCommand):
    help = 'Remove jobs e arquivos de saída mais antigos que N dias (padrão: 7).'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7,
                            help='Número de dias para manter os jobs.')

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options['days'])
        old_jobs = MediaJob.objects.filter(created_at__lt=cutoff)
        removed = 0
        for job in old_jobs:
            from core.tasks import _delete_job_files
            try:
                _delete_job_files(job)
            except Exception:
                pass
            job.delete()
            removed += 1
        self.stdout.write(self.style.SUCCESS(f'{removed} job(s) removido(s).'))
