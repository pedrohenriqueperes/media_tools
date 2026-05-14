from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('submit/', views.submit_job, name='submit_job'),
    path('submit/batch/', views.submit_batch, name='submit_batch'),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    path('job/<int:pk>/status/', views.job_status, name='job_status'),
    path('job/<int:pk>/payment/', views.job_payment, name='job_payment'),
    path('job/<int:pk>/check-payment/', views.check_payment, name='check_payment'),
    path('job/<int:pk>/delete/', views.delete_job, name='delete_job'),
    path('jobs/clear/', views.clear_jobs, name='clear_jobs'),
    path('webhook/', views.payment_webhook, name='payment_webhook'),
]
