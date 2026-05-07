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
        input_path = job.input_file.path
        job.input_size = Path(input_path).stat().st_size

        output_dir = Path(settings.MEDIA_ROOT) / 'outputs' / str(job_pk)
        output_dir.mkdir(parents=True, exist_ok=True)

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
