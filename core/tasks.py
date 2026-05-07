import subprocess
import zipfile
import threading
from pathlib import Path
from django.utils import timezone
from django.conf import settings


def process_job_async(job_pk):
    """Dispara process_job em uma thread separada."""
    t = threading.Thread(target=process_job, args=(job_pk,), daemon=True)
    t.start()


def process_job(job_pk):
    from .models import MediaJob
    job = MediaJob.objects.get(pk=job_pk)
    job.status = 'processing'
    job.save(update_fields=['status'])

    try:
        output_dir = Path(settings.MEDIA_ROOT) / 'outputs' / str(job_pk)
        output_dir.mkdir(parents=True, exist_ok=True)

        if job.job_type == 'batch_convert':
            # Único tipo sem input_file — lê direto do diretório de input
            p = job.job_params or {}
            target_fmt = p.get('target_format', 'WEBP').upper()
            input_dir = Path(settings.MEDIA_ROOT) / 'uploads' / f'batch_{job_pk}'
            files = [
                (f.name, f.read_bytes())
                for f in sorted(input_dir.iterdir())
                if f.is_file()
            ]
            zip_bytes = _batch_convert(files, target_fmt)
            zip_path = output_dir / 'converted.zip'
            zip_path.write_bytes(zip_bytes)
            job.output_path = f'outputs/{job_pk}/converted.zip'
            job.output_size = zip_path.stat().st_size
            job.frame_count = len(files)

        else:
            # Todos os outros tipos têm input_file obrigatório
            input_path = job.input_file.path
            job.input_size = Path(input_path).stat().st_size

            if job.job_type == 'frames':
                count = _extract_frames(input_path, output_dir)
                zip_path = output_dir / 'frames.zip'
                _zip_dir(output_dir, zip_path, pattern='frame_*.jpg')
                job.output_path = f'outputs/{job_pk}/frames.zip'
                job.output_size = zip_path.stat().st_size
                job.frame_count = count

            elif job.job_type == 'resize_image':
                out_file = output_dir / Path(input_path).name
                _resize_image(input_path, str(out_file))
                job.output_path = f'outputs/{job_pk}/{out_file.name}'
                job.output_size = out_file.stat().st_size

            elif job.job_type == 'resize_video':
                out_name = Path(input_path).stem + '_compressed.mp4'
                out_file = output_dir / out_name
                _resize_video(input_path, str(out_file))
                job.output_path = f'outputs/{job_pk}/{out_name}'
                job.output_size = out_file.stat().st_size

            elif job.job_type == 'convert_format':
                p = job.job_params or {}
                target_fmt = p.get('target_format', 'WEBP').upper()
                ext = 'jpg' if target_fmt == 'JPEG' else target_fmt.lower()
                out_name = Path(input_path).stem + f'.{ext}'
                out_file = output_dir / out_name
                converted = _convert_image_bytes(Path(input_path).read_bytes(), target_fmt)
                out_file.write_bytes(converted)
                job.output_path = f'outputs/{job_pk}/{out_name}'
                job.output_size = out_file.stat().st_size

            elif job.job_type == 'image_to_gif':
                out_name = Path(input_path).stem + '.gif'
                out_file = output_dir / out_name
                _image_to_gif(input_path, str(out_file))
                job.output_path = f'outputs/{job_pk}/{out_name}'
                job.output_size = out_file.stat().st_size

            elif job.job_type == 'video_to_gif':
                out_name = Path(input_path).stem + '.gif'
                out_file = output_dir / out_name
                p = job.job_params or {}
                _video_to_gif(
                    input_path, str(out_file),
                    fps=int(p.get('fps', 10)),
                    start=float(p.get('start', 0)),
                    duration=float(p['duration']) if p.get('duration') else None,
                    width=int(p['width']) if p.get('width') else None,
                )
                job.output_path = f'outputs/{job_pk}/{out_name}'
                job.output_size = out_file.stat().st_size

        job.status = 'done'
    except Exception as exc:
        job.status = 'error'
        job.error_message = str(exc)
    finally:
        job.finished_at = timezone.now()
        job.save(update_fields=[
            'status', 'output_path', 'input_size', 'output_size',
            'frame_count', 'error_message', 'finished_at',
        ])


def _zip_dir(directory, zip_path, pattern='*'):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(directory.glob(pattern)):
            zf.write(f, f.name)


def _extract_frames(video_path, output_dir):
    import cv2
    cap = cv2.VideoCapture(video_path)
    count = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        cv2.imwrite(str(output_dir / f'frame_{count:04d}.jpg'), frame)
        count += 1
    cap.release()
    return count


def _resize_image(input_path, output_path, max_size=800):
    from PIL import Image
    img = Image.open(input_path)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    ratio = min(max_size / img.size[0], max_size / img.size[1])
    if ratio < 1:
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    img.save(output_path, 'JPEG', quality=85, optimize=True)


def _resize_video(input_path, output_path):
    subprocess.run([
        'ffmpeg', '-i', input_path,
        '-c:v', 'h264', '-crf', '23', '-preset', 'medium',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        output_path,
    ], check=True)


_QUALITY = {
    'JPEG': {'quality': 95, 'optimize': True},
    'PNG':  {'optimize': True},
    'WEBP': {'quality': 95, 'method': 6},
}

_BATCH_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif'}


def _convert_image_bytes(image_bytes: bytes, target_format: str) -> bytes:
    from PIL import Image
    import io
    fmt = target_format.upper()
    img = Image.open(io.BytesIO(image_bytes))
    if fmt == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        mask = img.split()[-1] if img.mode == 'RGBA' else None
        bg.paste(img, mask=mask)
        img = bg
    out = io.BytesIO()
    img.save(out, format=fmt, **_QUALITY.get(fmt, {}))
    out.seek(0)
    return out.getvalue()


def _batch_convert(files, target_format: str) -> bytes:
    import io as _io
    fmt = target_format.upper()
    ext = 'jpg' if fmt == 'JPEG' else fmt.lower()
    buf = _io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, data in files:
            try:
                converted = _convert_image_bytes(data, fmt)
                base = Path(name).stem
                zf.writestr(f'{base}.{ext}', converted)
            except Exception:
                pass
    buf.seek(0)
    return buf.getvalue()


def _image_to_gif(input_path, output_path):
    from PIL import Image
    img = Image.open(input_path)
    img.save(output_path, 'GIF')


def _video_to_gif(input_path, output_path, fps=10, start=0, duration=None, width=None):
    from moviepy.video.io.VideoFileClip import VideoFileClip
    video = VideoFileClip(input_path)
    if width:
        ratio = width / video.w
        video = video.resized(ratio)
    if duration:
        video = video.subclipped(start, start + duration)
    elif start > 0:
        video = video.subclipped(start)
    video.write_gif(output_path, fps=fps)
    video.close()
