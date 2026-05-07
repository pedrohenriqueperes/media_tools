import subprocess
import os
from pathlib import Path

def compress_video(input_path, output_path=None, target_size_mb=50):
    try:
        if output_path is None:
            filename = Path(input_path).stem
            output_path = f"{filename}_compressed.mp4"
            
        # Get video duration and bitrate
        probe = subprocess.run([
            'ffmpeg', '-i', input_path,
            '-hide_banner'
        ], stderr=subprocess.PIPE)  # Simplified probe command
        
        print(f"Processing: {input_path}")
        
        # Compress video with reasonable settings
        command = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'h264',
            '-crf', '23',
            '-preset', 'medium',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            output_path
        ]
        
        subprocess.run(command, check=True)
        print(f"Compressed video saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")
        return False

def process_directory(directory_path):
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv'}
    processed = 0
    failed = 0
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            if Path(file).suffix.lower() in video_extensions:
                full_path = os.path.join(root, file)
                if compress_video(full_path):
                    processed += 1
                else:
                    failed += 1
    
    return processed, failed

if __name__ == "__main__":
    input_video_path = "videos/2.mp4"
    output_video_path = "videos/2_compressed.mp4"

    if compress_video(input_video_path, output_video_path):
        print(f"Successfully compressed {input_video_path} to {output_video_path}")
    else:
        print(f"Failed to compress {input_video_path}")