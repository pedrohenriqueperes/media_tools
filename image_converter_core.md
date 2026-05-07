# Image Converter — Core Logic

Lógica pura de conversão de imagens extraída do projeto Django, sem dependências do framework. Pronta para reusar em qualquer projeto Python.

---

## Requisitos

```txt
pillow==11.2.1
```

Para conversão em lote com ZIP:
```txt
pillow==11.2.1
# zipfile é stdlib do Python — sem dependência extra
```

Se precisar de auto-delete agendado (opcional):
```txt
celery==5.5.2
redis==6.2.0
```

---

## Formatos suportados

| Formato | Extensão | Notas |
|---------|----------|-------|
| JPEG    | `.jpg`   | Não suporta transparência (fundo branco aplicado automaticamente) |
| PNG     | `.png`   | Suporta transparência |
| WEBP    | `.webp`  | Suporta transparência |
| BMP     | `.bmp`   | |
| TIFF    | `.tiff`  | |
| GIF     | `.gif`   | |

---

## Conversão de imagem única

```python
from PIL import Image
import io

QUALITY_SETTINGS = {
    "JPEG": {"quality": 95, "optimize": True},
    "PNG":  {"optimize": True},
    "WEBP": {"quality": 95, "method": 6},
}

def convert_image(image_bytes: bytes, target_format: str) -> bytes:
    """
    Converte image_bytes para o formato alvo e retorna os bytes resultantes.

    Args:
        image_bytes: conteúdo binário da imagem original
        target_format: "JPEG" | "PNG" | "WEBP" | "BMP" | "TIFF" | "GIF"

    Returns:
        bytes da imagem convertida
    """
    target_format = target_format.upper()
    image = Image.open(io.BytesIO(image_bytes))

    # JPEG não suporta canal alpha — compõe sobre fundo branco
    if target_format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        mask = image.split()[-1] if image.mode == "RGBA" else None
        background.paste(image, mask=mask)
        image = background

    output = io.BytesIO()
    save_kwargs = QUALITY_SETTINGS.get(target_format, {})
    image.save(output, format=target_format, **save_kwargs)
    output.seek(0)
    return output.getvalue()
```

### Uso

```python
# A partir de um arquivo em disco
with open("foto.png", "rb") as f:
    original_bytes = f.read()

converted_bytes = convert_image(original_bytes, "WEBP")

with open("foto.webp", "wb") as f:
    f.write(converted_bytes)
```

```python
# A partir de um upload (Flask / FastAPI / etc.)
# Flask
converted = convert_image(request.files["image"].read(), "JPEG")

# FastAPI
async def upload(file: UploadFile):
    converted = convert_image(await file.read(), "PNG")
```

---

## Conversão em lote (retorna ZIP)

```python
from PIL import Image
import io
import os
import zipfile
from typing import List, Tuple

def convert_batch_to_zip(
    files: List[Tuple[str, bytes]],
    target_format: str,
    max_images: int = 100,
) -> bytes:
    """
    Converte múltiplas imagens e empacota em um ZIP em memória.

    Args:
        files: lista de (nome_do_arquivo, bytes_da_imagem)
        target_format: formato alvo para todas as imagens
        max_images: limite de imagens por lote

    Returns:
        bytes do arquivo ZIP

    Raises:
        ValueError: se o número de imagens exceder max_images
    """
    if len(files) > max_images:
        raise ValueError(
            f"Máximo de {max_images} imagens por lote. Recebidas: {len(files)}"
        )

    target_format = target_format.upper()
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for original_name, image_bytes in files:
            try:
                converted = convert_image(image_bytes, target_format)
                base_name = os.path.splitext(original_name)[0]
                output_name = f"{base_name}.{target_format.lower()}"
                zf.writestr(output_name, converted)
            except Exception as e:
                # Imagens com erro são ignoradas; trate conforme sua necessidade
                print(f"Erro em {original_name}: {e}")

    zip_buffer.seek(0)
    return zip_buffer.getvalue()
```

### Uso

```python
files = []
for path in ["a.png", "b.jpg", "c.webp"]:
    with open(path, "rb") as f:
        files.append((os.path.basename(path), f.read()))

zip_bytes = convert_batch_to_zip(files, "WEBP")

with open("converted_images.zip", "wb") as f:
    f.write(zip_bytes)
```

---

## Auto-delete de arquivos temporários (opcional — requer Celery + Redis)

Se o projeto usar Celery, use a task abaixo para apagar arquivos temporários após N segundos.

```python
# tasks.py
import os
import logging
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def delete_temp_file(file_path: str):
    """Remove um arquivo temporário do disco."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Arquivo removido: {file_path}")
            return True
    except Exception as e:
        logger.error(f"Erro ao remover {file_path}: {e}")
    return False
```

```python
# Agendando a remoção 3 minutos após salvar
delete_temp_file.apply_async(args=["/caminho/arquivo.webp"], countdown=180)
```

---

## Detecção de formato original

```python
from PIL import Image
import io

def get_image_info(image_bytes: bytes) -> dict:
    """Retorna metadados básicos da imagem."""
    image = Image.open(io.BytesIO(image_bytes))
    return {
        "format": image.format,       # ex: "PNG", "JPEG"
        "mode": image.mode,            # ex: "RGB", "RGBA"
        "width": image.size[0],
        "height": image.size[1],
        "size_bytes": len(image_bytes),
    }
```

---

## Notas

- **Transparência + JPEG**: Pillow não suporta canal alpha em JPEG. O código compõe automaticamente sobre fundo branco (`RGB 255,255,255`). Para preservar transparência use PNG ou WEBP.
- **Qualidade WEBP**: `method=6` é o nível máximo de compressão (mais lento, arquivo menor). Reduza para `method=0` se velocidade for prioridade.
- **GIF animado**: `Image.open` lê apenas o primeiro frame. Para preservar animação é necessário tratamento adicional com `ImageSequence`.
