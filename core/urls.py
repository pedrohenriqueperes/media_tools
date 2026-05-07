from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('submit/', views.submit_job, name='submit_job'),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    path('job/<int:pk>/status/', views.job_status, name='job_status'),
]
