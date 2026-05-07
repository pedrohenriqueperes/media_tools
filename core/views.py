from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import MediaJob
from .forms import MediaJobForm
from .tasks import process_job_async

FRAMES_PREVIEW_LIMIT = 30


@login_required
def dashboard(request):
    jobs = MediaJob.objects.filter(user=request.user)
    paginator = Paginator(jobs, 12)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/dashboard.html', {'page': page})


@login_required
def submit_job(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = MediaJobForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.user = request.user
            job.save()
            process_job_async(job.pk)
            if is_ajax:
                return JsonResponse({'job_pk': job.pk})
            return redirect('job_detail', pk=job.pk)
        else:
            if is_ajax:
                errors = {f: e.get_json_data() for f, e in form.errors.items()}
                return JsonResponse({'errors': errors}, status=400)

    else:
        form = MediaJobForm()
    return render(request, 'core/submit.html', {'form': form})


@login_required
def job_detail(request, pk):
    job = get_object_or_404(MediaJob, pk=pk, user=request.user)
    output_url = None
    frame_urls = []

    if job.status == 'done' and job.output_path:
        output_url = settings.MEDIA_URL + job.output_path

        if job.job_type == 'frames':
            output_dir = Path(settings.MEDIA_ROOT) / 'outputs' / str(job.pk)
            frames = sorted(output_dir.glob('frame_*.jpg'))[:FRAMES_PREVIEW_LIMIT]
            frame_urls = [
                settings.MEDIA_URL + f'outputs/{job.pk}/{f.name}' for f in frames
            ]

    return render(request, 'core/job_detail.html', {
        'job': job,
        'output_url': output_url,
        'frame_urls': frame_urls,
    })


@login_required
def job_status(request, pk):
    job = get_object_or_404(MediaJob, pk=pk, user=request.user)
    return JsonResponse({'status': job.status})
