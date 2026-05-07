from pathlib import Path
from django import forms
from .models import MediaJob

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv'}
MAX_UPLOAD_MB = 200


class MediaJobForm(forms.ModelForm):
    class Meta:
        model = MediaJob
        fields = ['job_type', 'input_file']
        widgets = {
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'input_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'job_type': 'Tipo de processamento',
            'input_file': 'Arquivo',
        }

    def clean(self):
        cleaned_data = super().clean()
        job_type = cleaned_data.get('job_type')
        f = cleaned_data.get('input_file')

        if not f or not job_type:
            return cleaned_data

        if f.size > MAX_UPLOAD_MB * 1024 * 1024:
            raise forms.ValidationError(f'Arquivo muito grande. Limite: {MAX_UPLOAD_MB} MB.')

        ext = Path(f.name).suffix.lower()
        if job_type in ('resize_image', 'image_to_gif') and ext not in IMAGE_EXTS:
            raise forms.ValidationError('Para este tipo, envie uma imagem (.jpg, .png, .webp, .bmp).')
        if job_type in ('resize_video', 'frames', 'video_to_gif') and ext not in VIDEO_EXTS:
            raise forms.ValidationError('Para este tipo, envie um vídeo (.mp4, .mov, .avi, .mkv).')

        return cleaned_data
