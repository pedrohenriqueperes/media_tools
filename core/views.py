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


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')


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
            if job.job_type == 'video_to_gif':
                job.job_params = {
                    k: request.POST.get(k)
                    for k in ('fps', 'start', 'duration', 'width')
                    if request.POST.get(k)
                }
            elif job.job_type == 'convert_format':
                job.job_params = {'target_format': request.POST.get('target_format', 'WEBP').upper()}
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
    convert_formats = [
        ('WEBP', 'Web'), ('JPEG', 'Foto'), ('PNG', 'Transp.'),
        ('GIF', 'GIF'), ('BMP', 'Bitmap'), ('TIFF', 'Alta res.'),
    ]
    return render(request, 'core/submit.html', {'form': form, 'convert_formats': convert_formats})


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


BATCH_MAX = 100
BATCH_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif'}
BATCH_TARGET_FORMATS = {'JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF', 'GIF'}


@login_required
def submit_batch(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        files = request.FILES.getlist('files')
        target_format = request.POST.get('target_format', 'WEBP').upper()

        def err(msg):
            if is_ajax:
                return JsonResponse({'errors': {'__all__': [{'message': msg}]}}, status=400)
            messages.error(request, msg)
            return render(request, 'core/submit_batch.html',
                          {'target_format': target_format})

        if not files:
            return err('Selecione ao menos uma imagem.')
        if len(files) > BATCH_MAX:
            return err(f'Máximo de {BATCH_MAX} imagens por lote.')
        if target_format not in BATCH_TARGET_FORMATS:
            return err('Formato de destino inválido.')
        for f in files:
            if Path(f.name).suffix.lower() not in BATCH_IMAGE_EXTS:
                return err(f'"{f.name}" não é uma imagem suportada.')

        total_size = sum(f.size for f in files)

        job = MediaJob.objects.create(
            user=request.user,
            job_type='batch_convert',
            input_size=total_size,
            job_params={'target_format': target_format, 'file_count': len(files)},
        )

        input_dir = Path(settings.MEDIA_ROOT) / 'uploads' / f'batch_{job.pk}'
        input_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            dest = input_dir / Path(f.name).name
            with open(dest, 'wb') as out:
                for chunk in f.chunks():
                    out.write(chunk)

        process_job_async(job.pk)

        if is_ajax:
            return JsonResponse({'job_pk': job.pk})
        return redirect('job_detail', pk=job.pk)

    formats = [
        ('WEBP',  'Web'),
        ('JPEG',  'Foto'),
        ('PNG',   'Transparência'),
        ('GIF',   'Animação'),
        ('BMP',   'Bitmap'),
        ('TIFF',  'Alta res.'),
    ]
    return render(request, 'core/submit_batch.html', {
        'formats': formats,
        'target_format': request.POST.get('target_format', 'WEBP'),
    })


@login_required
def delete_job(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    job = get_object_or_404(MediaJob, pk=pk, user=request.user)
    job.delete()
    return JsonResponse({'ok': True})


@login_required
def clear_jobs(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    MediaJob.objects.filter(user=request.user).delete()
    return JsonResponse({'ok': True})
