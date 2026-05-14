from django.contrib import admin
from .models import MediaJob, JobPricing


@admin.register(MediaJob)
class MediaJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'job_type', 'status', 'payment_status', 'created_at']
    list_filter = ['job_type', 'status', 'payment_status']
    search_fields = ['user__email', 'payment_transaction_id']
    readonly_fields = ['payment_transaction_id', 'payment_qr_code', 'payment_clipboard']


@admin.register(JobPricing)
class JobPricingAdmin(admin.ModelAdmin):
    list_display = ['job_type', 'price']
    list_editable = ['price']
