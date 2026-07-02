import os
import json
import urllib.request
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Define Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "pose_landmarker_heavy.task")
INPUT_DIR = os.path.join(BASE_DIR, "data", "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")

# URLs for setup
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
SAMPLE_IMAGES = {
    "pushup.jpg": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?q=80&w=1000",
    "fitness.jpg": "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?q=80&w=1000",
    "yoga.jpg": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?q=80&w=1000"
}

# Pose connections mapping according to MediaPipe documentation
POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),  # Upper body (shoulders, arms)
    (11, 23), (12, 24), (23, 24),                      # Torso (shoulders to hips, hip connection)
    (23, 25), (25, 27), (24, 26), (26, 28),           # Legs (hips to knees, knees to ankles)
    (27, 29), (29, 31), (27, 31),                      # Left foot
    (28, 30), (30, 32), (28, 32),                      # Right foot
    (15, 17), (15, 19), (15, 21), (17, 19),            # Left hand / fingers
    (16, 18), (16, 20), (16, 22), (18, 20),            # Right hand / fingers
    (0, 1), (1, 2), (2, 3), (3, 7),                    # Left eye path to ear
    (0, 4), (4, 5), (5, 6), (6, 8),                    # Right eye path to ear
    (9, 10)                                            # Mouth edges
]

# Mapping landmark indices to descriptive names
LANDMARK_NAMES = {
    0: "NOSE", 1: "LEFT_EYE_INNER", 2: "LEFT_EYE", 3: "LEFT_EYE_OUTER",
    4: "RIGHT_EYE_INNER", 5: "RIGHT_EYE", 6: "RIGHT_EYE_OUTER",
    7: "LEFT_EAR", 8: "RIGHT_EAR", 9: "MOUTH_LEFT", 10: "MOUTH_RIGHT",
    11: "LEFT_SHOULDER", 12: "RIGHT_SHOULDER", 13: "LEFT_ELBOW", 14: "RIGHT_ELBOW",
    15: "LEFT_WRIST", 16: "RIGHT_WRIST", 17: "LEFT_PINKY", 18: "RIGHT_PINKY",
    19: "LEFT_INDEX", 20: "RIGHT_INDEX", 21: "LEFT_THUMB", 22: "RIGHT_THUMB",
    23: "LEFT_HIP", 24: "RIGHT_HIP", 25: "LEFT_KNEE", 26: "RIGHT_KNEE",
    27: "LEFT_ANKLE", 28: "RIGHT_ANKLE", 29: "LEFT_HEEL", 30: "RIGHT_HEEL",
    31: "LEFT_FOOT_INDEX", 32: "RIGHT_FOOT_INDEX"
}

def is_landmark_visible(lm, threshold=0.5):
    """Returns True if the landmark's visibility confidence is above the threshold."""
    return getattr(lm, 'visibility', 0.0) >= threshold

def ensure_directory(path):
    """Creates a directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def download_file(url, destination_path, file_description):
    """Downloads a file from a URL with a custom User-Agent to avoid 403 Forbidden errors."""
    if os.path.exists(destination_path):
        print(f"{file_description} already exists at {destination_path}.")
        return

    print(f"Downloading {file_description} from {url}...")
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
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
                    else:
                        print(f"\rDownloading: {read_so_far} bytes received", end="")
            print("\nDownload complete!")
    except Exception as e:
        print(f"\nError downloading {file_description}: {e}")
        # Clean up partial download if failed
        if os.path.exists(destination_path):
            try:
                os.remove(destination_path)
            except OSError:
                pass
        raise e

def setup_environment():
    """Checks and retrieves required folders, model binary, and input photos."""
    ensure_directory(INPUT_DIR)
    ensure_directory(OUTPUT_DIR)
    
    # Download heavy pose estimation model
    download_file(MODEL_URL, MODEL_PATH, "MediaPipe Heavy Pose Model")

    # Download calisthenics test images
    for filename, url in SAMPLE_IMAGES.items():
        dest = os.path.join(INPUT_DIR, filename)
        download_file(url, dest, f"Sample Calisthenics Image ({filename})")

def process_images():
    """Initializes the MediaPipe Pose Landmarker detector and processes all input images."""
    print("\nInitializing MediaPipe Pose Landmarker...")
    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        output_segmentation_masks=False
    )
    
    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        # Find all images in the input directory
        valid_extensions = ('.jpg', '.jpeg', '.png')
        input_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(valid_extensions)]
        
        if not input_files:
            print("No input images found to process.")
            return

        for filename in input_files:
            input_path = os.path.join(INPUT_DIR, filename)
            print(f"\nProcessing: {filename}...")
            
            # 1. Load image using OpenCV for manipulation and MediaPipe for inference
            cv_img = cv2.imread(input_path)
            if cv_img is None:
                print(f"Error: Could not load image {filename}")
                continue
                
            # Create MediaPipe Image object from OpenCV image file
            mp_image = mp.Image.create_from_file(input_path)
            
            # 2. Run inference
            result = landmarker.detect(mp_image)
            
            # 3. Handle results
            if not result.pose_landmarks:
                print(f"No pose landmarks detected in {filename}")
                continue
                
            print(f"Successfully detected pose in {filename}!")
            
            # Standardize outputs format (supports multiple detected poses, normally 1)
            landmarks = result.pose_landmarks[0]
            world_landmarks = result.pose_world_landmarks[0] if result.pose_world_landmarks else []

            # 4. Save JSON detailed data
            landmark_data = []
            for i, lm in enumerate(landmarks):
                # Match corresponding world landmark if available
                world_lm = world_landmarks[i] if i < len(world_landmarks) else None
                
                lm_entry = {
                    "index": i,
                    "name": LANDMARK_NAMES.get(i, "UNKNOWN"),
                    "x_normalized": lm.x,
                    "y_normalized": lm.y,
                    "z_normalized": lm.z,
                    "visibility": lm.visibility,
                    "presence": lm.presence,
                    "x_world_meters": world_lm.x if world_lm else None,
                    "y_world_meters": world_lm.y if world_lm else None,
                    "z_world_meters": world_lm.z if world_lm else None,
                }
                landmark_data.append(lm_entry)

            base_name = os.path.splitext(filename)[0]
            json_output_path = os.path.join(OUTPUT_DIR, f"{base_name}_landmarks.json")
            with open(json_output_path, "w") as f:
                json.dump(landmark_data, f, indent=4)
            print(f"Saved landmarks JSON to: {json_output_path}")

            # 5. Draw landmarks & skeleton on image
            annotated_img = cv_img.copy()
            h, w, _ = cv_img.shape

            # Calculate pixel positions for drawing connections
            pixel_points = {}
            for i, lm in enumerate(landmarks):
                # Filter out landmarks that are not visible to clean up lines and occluded parts
                if is_landmark_visible(lm, threshold=0.5):
                    # MediaPipe normalizes coordinates (0.0 to 1.0). Convert to pixel space.
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    pixel_points[i] = (cx, cy)

            # Draw connection lines (Skeleton)
            # Use cyan/blue lines with high aesthetic contrast
            line_color = (255, 191, 0) # Cyan in BGR (or light blue)
            for start_idx, end_idx in POSE_CONNECTIONS:
                if start_idx in pixel_points and end_idx in pixel_points:
                    cv2.line(
                        annotated_img,
                        pixel_points[start_idx],
                        pixel_points[end_idx],
                        color=line_color,
                        thickness=3,
                        lineType=cv2.LINE_AA
                    )

            # Draw landmark dots
            # Red/magenta for joints, green for head
            for i, point in pixel_points.items():
                # Color code: head features vs limb joints
                if i < 11:
                    dot_color = (0, 255, 0)  # Green for face landmarks
                    radius = 4
                else:
                    dot_color = (0, 0, 255)  # Red for body joints
                    radius = 6
                
                # Draw outer glow circle
                cv2.circle(annotated_img, point, radius + 2, (255, 255, 255), thickness=-1, lineType=cv2.LINE_AA)
                # Draw inner solid circle
                cv2.circle(annotated_img, point, radius, dot_color, thickness=-1, lineType=cv2.LINE_AA)

            # 6. Save annotated image output file
            img_output_path = os.path.join(OUTPUT_DIR, f"{base_name}_annotated.jpg")
            cv2.imwrite(img_output_path, annotated_img)
            print(f"Saved annotated image to: {img_output_path}")

if __name__ == "__main__":
    print("=== MediaPipe Pose Estimation Test Utility ===")
    setup_environment()
    process_images()
    print("\nAll tasks completed successfully!")
