# Vision Module (TSK-03)

2D pose keypoint extraction using MediaPipe Pose Landmarker for push-up form analysis.

## Setup
```bash
pip install -r src/vision/requirements.txt
```

## Usage
```python
from src.vision.pose_extractor import extract_landmarks

# Returns list of per-frame landmark dicts
landmarks = extract_landmarks("path/to/video.mp4")
```

The coordinates are normalized per axis, so angles measured on them are distorted
unless the frame is square. When feeding the biomechanics engine, also pass the
frame size:
```python
from src.vision.pose_extractor import extract_landmarks_with_frame_size
from src.biomechanics.pushup_rules import evaluate_pushup_stream

landmarks, (frame_width, frame_height) = extract_landmarks_with_frame_size("path/to/video.mp4")
result = evaluate_pushup_stream(landmarks, frame_width, frame_height)
```

## Data Contract
Returns normalized `(x, y)` coordinates per frame (automatically selects visible side in sagittal view):
```python
{
    "shoulder": (x, y),  # Joint 11/12
    "elbow": (x, y),     # Joint 13/14
    "wrist": (x, y),     # Joint 15/16
    "hip": (x, y),       # Joint 23/24
    "knee": (x, y),      # Joint 25/26
    "ankle": (x, y),     # Joint 27/28
}
```

## Benchmark CLI (DoD < 35ms)
```bash
python src/vision/pose_extractor.py path/to/video.mp4
```
- **Observed CPU latency**: ~18.3 ms/frame (**PASS [✓]**)
