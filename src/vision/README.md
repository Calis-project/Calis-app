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

## Data Contract
Returns normalized `(x, y)` coordinates per frame (automatically selects visible side in sagittal view):
```python
{
    "shoulder": (x, y),  # Joint 11/12
    "elbow": (x, y),     # Joint 13/14
    "wrist": (x, y),     # Joint 15/16
    "hip": (x, y),       # Joint 23/24
    "ankle": (x, y),     # Joint 27/28
}
```

## Benchmark CLI (DoD < 35ms)
```bash
python src/vision/pose_extractor.py path/to/video.mp4
```
- **Observed CPU latency**: ~18.3 ms/frame (**PASS [✓]**)
