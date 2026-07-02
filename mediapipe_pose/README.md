# MediaPipe Pose Estimation Demo

This is a standalone Python utility designed to demonstrate and test **Google MediaPipe's modern Tasks API** for human pose landmark detection on calisthenics/sports images.

The utility processes input photos, detects 33 landmark points, and outputs:
1. An annotated image displaying the skeleton layout.
2. A detailed JSON file containing coordinates (both normalized pixel space and 3D world meters) for debugging.

---

## Directory Layout
```
mediapipe_pose/
├── .venv/                      # Local Python virtual environment
├── data/
│   ├── input/                  # Put source images here
│   └── output/                 # Generated annotated images & JSON coordinates
├── pose_demo.py                # Main script execution entrypoint
├── requirements.txt            # Package dependencies list
└── README.md                   # This instruction file
```

---

## Setup & Execution

### 1. Configure the Virtual Environment
Navigate to this directory in your terminal and run:

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Demo Script
To download the model weights file (`pose_landmarker_heavy.task`), download the test calisthenics images, and run inference, run:

```bash
python pose_demo.py
```

### 3. Review Outputs
The script automatically:
- Populates `data/input/` with sample calisthenics images.
- Evaluates each image and saves:
  - `data/output/<image_name>_annotated.jpg` (Visual representation)
  - `data/output/<image_name>_landmarks.json` (Numerical coordinate data)
