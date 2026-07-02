---
name: mediapipe-tasks-usage
description: Guides the agent on how to use the modern MediaPipe Tasks API (v0.10.x+) for Pose Landmarking in Python.
---

# MediaPipe Tasks API Usage Guide

## Key Information
- The legacy `mp.solutions.pose` API is deprecated in favor of the new **MediaPipe Tasks API** (`mediapipe.tasks.python.vision.PoseLandmarker`).
- A pre-trained model file (`.task` extension) is required. The default heavy variant is `pose_landmarker_heavy.task`.

## Code Pattern Instructions

### 1. Imports
```python
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
```

### 2. Initialization
```python
base_options = python.BaseOptions(model_asset_path='pose_landmarker_heavy.task')
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    output_segmentation_masks=False
)
detector = vision.PoseLandmarker.create_from_options(options)
```

### 3. Running Inference
To load an image, use MediaPipe's custom image loader:
```python
# From file
mp_image = mp.Image.create_from_file("input.jpg")

# From numpy/opencv (SRGB format is required)
# mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2_image)

detection_result = detector.detect(mp_image)
```

### 4. Extracting Outputs
The `detection_result` (instance of `PoseLandmarkerResult`) contains:
- `pose_landmarks`: A list of lists of normalized landmarks (each landmark has `x`, `y`, `z`, `visibility`, `presence`).
- `pose_world_landmarks`: A list of lists of 3D landmarks in meters centered around the origin.

### 5. Drawing Landmarks
You can iterate over the 33 landmarks and draw them using OpenCV:
- Landmark index ranges from 0 to 32.
- Key connections map:
  - Left arm: 11-13, 13-15
  - Right arm: 12-14, 14-16
  - Left leg: 23-25, 25-27, 27-31, 27-29, 29-31
  - Right leg: 24-26, 26-28, 28-32, 28-30, 30-32
  - Torso: 11-12, 12-24, 24-23, 23-11
