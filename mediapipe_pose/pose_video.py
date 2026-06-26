import os
import sys
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Define Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "pose_landmarker_heavy.task")
INPUT_DIR = os.path.join(BASE_DIR, "data", "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")

# URL to download model if missing
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"

# Pose connections mapping
POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),  # Upper body
    (11, 23), (12, 24), (23, 24),                      # Torso
    (23, 25), (25, 27), (24, 26), (26, 28),           # Legs
    (27, 29), (29, 31), (27, 31),                      # Left foot
    (28, 30), (30, 32), (28, 32),                      # Right foot
    (15, 17), (15, 19), (15, 21), (17, 19),            # Left hand
    (16, 18), (16, 20), (16, 22), (18, 20),            # Right hand
    (0, 1), (1, 2), (2, 3), (3, 7),                    # Left eye path to ear
    (0, 4), (4, 5), (5, 6), (6, 8),                    # Right eye path to ear
    (9, 10)                                            # Mouth
]

def is_landmark_visible(lm, threshold=0.5):
    """Returns True if the landmark's visibility confidence is above the threshold."""
    return getattr(lm, 'visibility', 0.0) >= threshold

def ensure_directory(path):
    """Creates a directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)

def download_file(url, destination_path, file_description):
    """Downloads the MediaPipe model weights with custom User-Agent to bypass blocks."""
    if os.path.exists(destination_path):
        return

    print(f"Downloading {file_description} from {url}...")
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            total_size = int(response.info().get('Content-Length', 0))
            block_size = 8192
            read_so_far = 0
            
            with open(destination_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    f.write(buffer)
                    read_so_far += len(buffer)
                    if total_size > 0:
                        percent = min(100, int(read_so_far * 100 / total_size))
                        print(f"\rDownloading: {percent}% completed", end="")
            print("\nDownload complete!")
    except Exception as e:
        print(f"\nError downloading {file_description}: {e}")
        if os.path.exists(destination_path):
            try:
                os.remove(destination_path)
            except OSError:
                pass
        raise e

def process_video(input_video_path, output_video_path):
    """Processes a video frame-by-frame and writes annotated outputs using VIDEO mode."""
    # 1. Open video
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {input_video_path}")
        return

    # Read video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if fps <= 0:
        fps = 30.0  # Fallback FPS
        
    print(f"Video Properties: Resolution {width}x{height} | {fps} FPS | Total Frames: {total_frames}")

    # 2. Configure Video Writer
    # 'mp4v' codec is highly compatible with Windows/macOS media players
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # 3. Setup MediaPipe Landmarker in VIDEO mode
    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO
    )

    print("\nProcessing video frames...")
    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        frame_index = 0
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            # A. Calculate the monotonic timestamp in milliseconds
            timestamp_ms = int((frame_index / fps) * 1000)

            # B. Convert BGR (OpenCV) to RGB (MediaPipe)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # C. Detect pose for current video frame
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            # D. Render annotations if pose detected
            annotated_frame = frame.copy()
            if result.pose_landmarks:
                landmarks = result.pose_landmarks[0]

                # Calculate pixel positions for visible joints
                pixel_points = {}
                for i, lm in enumerate(landmarks):
                    if is_landmark_visible(lm, threshold=0.5):
                        cx, cy = int(lm.x * width), int(lm.y * height)
                        pixel_points[i] = (cx, cy)

                # Draw connections (Skeleton lines)
                line_color = (255, 191, 0)  # Cyan/Blue color
                for start_idx, end_idx in POSE_CONNECTIONS:
                    if start_idx in pixel_points and end_idx in pixel_points:
                        cv2.line(
                            annotated_frame,
                            pixel_points[start_idx],
                            pixel_points[end_idx],
                            color=line_color,
                            thickness=3,
                            lineType=cv2.LINE_AA
                        )

                # Draw landmark dots
                for i, point in pixel_points.items():
                    if i < 11:
                        dot_color = (0, 255, 0)  # Green for face landmarks
                        radius = 4
                    else:
                        dot_color = (0, 0, 255)  # Red for body joints
                        radius = 6
                    
                    # Outer white circle for aesthetic outline, followed by solid inner circle
                    cv2.circle(annotated_frame, point, radius + 2, (255, 255, 255), thickness=-1, lineType=cv2.LINE_AA)
                    cv2.circle(annotated_frame, point, radius, dot_color, thickness=-1, lineType=cv2.LINE_AA)

            # E. Write frame to file
            out.write(annotated_frame)
            
            frame_index += 1
            if total_frames > 0:
                percent = int((frame_index / total_frames) * 100)
                print(f"\rProgress: {frame_index}/{total_frames} frames ({percent}%)", end="")
            else:
                print(f"\rProgress: {frame_index} frames processed", end="")

    print("\nWriting finished!")
    cap.release()
    out.release()

if __name__ == "__main__":
    print("=== MediaPipe Video Pose Estimation Utility ===")
    
    # Check environment
    ensure_directory(INPUT_DIR)
    ensure_directory(OUTPUT_DIR)
    download_file(MODEL_URL, MODEL_PATH, "MediaPipe Heavy Pose Model")

    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')

    # Determine which videos to process based on command line arguments
    if len(sys.argv) > 1:
        # Collect video names from arguments (split by commas/spaces)
        raw_targets = []
        for arg in sys.argv[1:]:
            parts = [p.strip() for p in arg.split(',') if p.strip()]
            raw_targets.extend(parts)

        # Resolve files in data/input/
        videos_to_process = []
        for target in raw_targets:
            target_path = os.path.join(INPUT_DIR, target)
            if os.path.exists(target_path) and target.lower().endswith(video_extensions):
                videos_to_process.append(target)
            else:
                # Try adding standard extensions
                found = False
                for ext in video_extensions:
                    candidate = target if target.lower().endswith(ext) else f"{target}{ext}"
                    candidate_path = os.path.join(INPUT_DIR, candidate)
                    if os.path.exists(candidate_path):
                        videos_to_process.append(candidate)
                        found = True
                        break
                if not found:
                    print(f"Warning: Specified video '{target}' was not found in 'data/input/'. Skipping.")
    else:
        # If no arguments, list all supported videos in input directory
        videos_to_process = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(video_extensions)]

    if not videos_to_process:
        print("\n[!] No valid input video files to process.")
        print("Please place your video files inside:")
        print(f"    {INPUT_DIR}")
        print("Then run this script again (optionally specifying filenames as arguments).")
    else:
        print(f"\nQueueing {len(videos_to_process)} video(s) for processing:")
        for idx, video in enumerate(videos_to_process, 1):
            print(f"  {idx}. {video}")

        for video in videos_to_process:
            input_path = os.path.join(INPUT_DIR, video)
            base_name = os.path.splitext(video)[0]
            output_filename = f"{base_name}_annotated.mp4"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            print(f"\nProcessing: {video}")
            print(f"Target Output: {output_path}")
            process_video(input_path, output_path)
            
        print("\nAll video processing completed successfully!")
