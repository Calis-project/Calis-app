# Severity Limitations of MediaPipe Biomechanical Engines

Key limitations of using deterministic biomechanical rules on MediaPipe pose coordinates to grade heterogeneous calisthenics videos on a full spectrum:

### 1. Perspective Distortion & Camera Angle Sensitivity
* **Description**: Camera placement (diagonal, front, high, or low angles) changes the 2D visual projection of the body. Calculating angles in 2D ignores depth, while 3D estimation is too noisy, leading to incorrect grading based solely on camera viewpoint.

### 2. Unstable Single-Camera Depth ($Z$-axis) Estimation
* **Description**: MediaPipe estimates 3D depth from a single 2D frame. This depth coordinate is highly unstable, introducing $\pm 10^\circ$ of noise in joint angles and triggering false form violations.

### 3. Occlusion and Self-Occlusion
* **Description**: During exercises like pushups or squats, limbs or joints (e.g., the far wrist or hip) are frequently blocked by the body or ground, causing the model to guess coordinates and produce severe tracking drift.

### 4. Anthropometric & Mobility Differences
* **Description**: Fixed angular thresholds do not account for individual body proportions (e.g., long vs. short limbs) or natural mobility differences, falsely marking safe, valid variations as "wrong" form.

### 5. Landmark Shift from Clothing and Lighting
* **Description**: Loose clothing, shadows, or low-contrast backgrounds cause MediaPipe to misplace key joints (e.g., shifting the shoulder to the collarbone), corrupting the math behind the heuristics.
