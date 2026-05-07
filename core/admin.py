from django.contrib import admin
from .models import MediaJob


@admin.register(MediaJob)
class MediaJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'job_type', 'status', 'created_at', 'finished_at']
    list_filter = ['job_type', 'status']
    search_fields = ['user__email']
