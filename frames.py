import cv2
import os

def extract_frames(video_path, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Read the video
    video = cv2.VideoCapture(video_path)
    
    # Get video properties
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Initialize frame counter
    count = 0
    
    print(f"Extracting frames from video...")
    print(f"Total frames: {frame_count}")
    
    while True:
        success, frame = video.read()
        
        if not success:
            break
        
        frame_name = f"frame_{count:04d}.jpg"
        frame_path = os.path.join(output_folder, frame_name)
        cv2.imwrite(frame_path, frame)
        
        count += 1
        # Show progress percentage every 100 frames
        if count % 100 == 0:
            progress = (count / frame_count) * 100
            print(f"Progress: {progress:.1f}% ({count} frames)")
    
    video.release()
    print(f"Extraction complete! {count} frames saved to {output_folder}")

if __name__ == "__main__":
    video_path = "/Users/php/Projetos/resize/video.MP4"
    output_folder = "pitchuca2"
    extract_frames(video_path, output_folder)