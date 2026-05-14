from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import MediaJob, JobPricing
from .forms import MediaJobForm
from .tasks import process_job_task
from .payments import generate_pix_payment, verify_pix_payment

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
            
            # Verificar Preço
            pricing = JobPricing.objects.filter(job_type=job.job_type).first()
            if pricing and pricing.price > 0:
                job.payment_status = 'pending'
                job.save()
                if is_ajax:
                    return JsonResponse({'payment_required': True, 'job_pk': job.pk})
                return redirect('job_payment', pk=job.pk)
            
            job.save()
            process_job_task.delay(job.pk)
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

        # Verificar Preço
        pricing = JobPricing.objects.filter(job_type=job.job_type).first()
        if pricing and pricing.price > 0:
            job.payment_status = 'pending'
            job.save()
            if is_ajax:
                return JsonResponse({'payment_required': True, 'job_pk': job.pk})
            return redirect('job_payment', pk=job.pk)

        process_job_task.delay(job.pk)

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


@login_required
def job_payment(request, pk):
    job = get_object_or_404(MediaJob, pk=pk, user=request.user)
    
    if job.payment_status == 'paid':
        return redirect('job_detail', pk=job.pk)
    
    pricing = get_object_or_404(JobPricing, job_type=job.job_type)
    
    # Se ainda não gerou o pagamento ou se o cache expirou/falhou
    if not job.payment_transaction_id:
        payment_data = generate_pix_payment(
            pricing.price, 
            f"Resize Job {job.pk} - {job.get_job_type_display()}",
            request.user.email
        )
        
        if payment_data and 'transaction_id' in payment_data:
            job.payment_transaction_id = payment_data['transaction_id']
            job.payment_qr_code = payment_data['qrcode']
            job.payment_clipboard = payment_data['clipboard']
            job.save()
        else:
            messages.error(request, "Erro ao gerar o PIX. Verifique os logs do servidor ou tente novamente.")
            return redirect('dashboard')

    return render(request, 'core/job_payment.html', {
        'job': job,
        'price': pricing.price,
    })


@login_required
def check_payment(request, pk):
    job = get_object_or_404(MediaJob, pk=pk, user=request.user)
    
    if job.payment_status == 'paid':
        return JsonResponse({'status': 'approved'})
    
    if not job.payment_transaction_id:
        return JsonResponse({'status': 'error', 'message': 'No transaction ID'}, status=400)
    
    status_data = verify_pix_payment(job.payment_transaction_id)
    
    if status_data and status_data.get('status') == 'approved':
        job.payment_status = 'paid'
        job.save()
        # Dispara o processamento agora que está pago
        process_job_task.delay(job.pk)
        return JsonResponse({'status': 'approved'})
    
    return JsonResponse({'status': status_data.get('status', 'pending') if status_data else 'pending'})


@csrf_exempt
@require_POST
def payment_webhook(request):
    """
    Recebe notificações automáticas da API de pagamentos (Mercado Pago)
    quando o status de uma transação muda.
    Espera JSON: {"transaction_id": "...", "status": "approved"}
    """
    import json

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    transaction_id = data.get('transaction_id')
    status = data.get('status')

    if not transaction_id:
        return JsonResponse({'error': 'Missing transaction_id'}, status=400)

    try:
        job = MediaJob.objects.get(payment_transaction_id=str(transaction_id))
    except MediaJob.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)

    if job.payment_status == 'paid':
        return JsonResponse({'ok': True, 'message': 'Already paid'})

    if status == 'approved':
        job.payment_status = 'paid'
        job.save(update_fields=['payment_status'])
        process_job_task.delay(job.pk)
        return JsonResponse({'ok': True, 'message': 'Payment confirmed, processing started'})

    if status in ('cancelled', 'rejected'):
        job.payment_status = 'failed'
        job.save(update_fields=['payment_status'])
        return JsonResponse({'ok': True, 'message': f'Payment marked as {status}'})

    return JsonResponse({'ok': True, 'message': f'Status received: {status}'})

