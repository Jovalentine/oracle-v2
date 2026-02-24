import cv2
from PIL import Image

def extract_keyframes(video_path, max_frames=15):
    """
    Extracts evenly spaced frames from a video to send to Gemini.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video at {video_path}")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Avoid division by zero on corrupted files
    if fps == 0 or total_frames == 0:
        fps = 30
        total_frames = 300

    # Calculate the interval to skip frames so we end up with exactly `max_frames`
    interval = max(1, total_frames // max_frames)
    
    frames = []
    timestamps = []
    
    count = 0
    while cap.isOpened() and len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        if count % interval == 0:
            # Convert BGR (OpenCV) to RGB (PIL)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            
            frames.append(pil_img)
            timestamps.append(round(count / fps, 1))
            
        count += 1
        
    cap.release()
    return frames, fps