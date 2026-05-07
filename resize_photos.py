import os
from PIL import Image
from pathlib import Path

def compress_image(image_path, max_size=800):
    try:
        img = Image.open(image_path)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            
        # Calculate new dimensions while maintaining aspect ratio
        ratio = min(max_size/float(img.size[0]), max_size/float(img.size[1]))
        if ratio < 1:
            new_size = tuple([int(x*ratio) for x in img.size])
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save with optimized quality
        img.save(image_path, 'JPEG', quality=85, optimize=True)
        return True
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return False

def process_directory(directory_path):
    image_extensions = {'.jpg', '.jpeg', '.png'}
    processed = 0
    failed = 0
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            if Path(file).suffix.lower() in image_extensions:
                full_path = os.path.join(root, file)
                if compress_image(full_path):
                    processed += 1
                else:
                    failed += 1
    
    return processed, failed

if __name__ == "__main__":
    media_path = "banner"  # Adjust this path as needed
    processed, failed = process_directory(media_path)
    print(f"Processed {processed} images successfully")
    print(f"Failed to process {failed} images")
