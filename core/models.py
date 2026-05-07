from django.db import models
from django.contrib.auth.models import User


class MediaJob(models.Model):
    TYPE_CHOICES = [
        ('frames', 'Extração de Frames'),
        ('resize_image', 'Redução de Imagem'),
        ('resize_video', 'Redução de Vídeo'),
        ('convert_format', 'Converter Formato de Imagem'),
        ('image_to_gif', 'Imagem para GIF'),
        ('video_to_gif', 'Vídeo para GIF'),
        ('batch_convert', 'Conversão em Lote'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Aguardando'),
        ('processing', 'Processando'),
        ('done', 'Concluído'),
        ('error', 'Erro'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    job_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    input_file = models.FileField(upload_to='uploads/', null=True, blank=True)
    output_path = models.CharField(max_length=500, blank=True)
    input_size = models.PositiveBigIntegerField(null=True, blank=True)
    output_size = models.PositiveBigIntegerField(null=True, blank=True)
    frame_count = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    job_params = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_job_type_display()} — {self.user} — {self.status}"

    @property
    def savings_pct(self):
        if self.input_size and self.output_size and self.input_size > 0:
            return round((1 - self.output_size / self.input_size) * 100)
        return None
