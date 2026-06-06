# Core Architecture

```text
[ User Camera (Video Capture) ]
                |
                v
+----------------------------------------------------------+
| 1. EDGE COMPUTE LAYER (On-Device Client iOS/Android)    |
|    - Google MediaPipe Pose / YOLO-Pose Web Assembly     |
|    - Tracks 33 skeletal landmarks in real time          |
|    - Drops raw video frames immediately after capture   |
+---------------------------+------------------------------+
                            |
                            v
       [Lightweight Telemetry Payload (JSON Vectors)]
                            |
                            v
+----------------------------------------------------------+
| 2. BIOMECHANICAL HEURISTICS ENGINE (Serverless / VM)    |
|    - Geometric calculations (vector dot products)       |
|    - Checks angles, velocity, and range of motion       |
|    - Flags deterministic structural safety violations   |
+---------------------------+------------------------------+
                            |
                            v
          [Structured Text Log / State Evaluation]
                            |
                            v
+----------------------------------------------------------+
| 3. COGNITIVE ORCHESTRATION LAYER (LLM API)              |
|    - Evaluates performance text payload via LLM         |
|    - Dynamically modifies upcoming training schema      |
|    - Synthesizes empathetic, precise coaching feedback  |
+----------------------------------------------------------+
```

## 3. Data Flow Specification

### Input (Edge Device)

Client-side processing tracks spatial coordinates over time:

```json
{
  "exercise": "pull_up",
  "frame_rate": 30,
  "telemetry": [
    {
      "timestamp_ms": 330,
      "landmarks": {
        "left_shoulder": [x, y, z, visibility],
        "left_elbow": [x, y, z, visibility],
        "left_wrist": [x, y, z, visibility]
      }
    }
  ]
}
```

### Transformation (Heuristics Engine)

The server maps the vector coordinates to simple joint metrics:

$$
\theta = \arccos\left(
  \frac{\vec{\mathbf{u}} \cdot \vec{\mathbf{v}}}
  {\|\vec{\mathbf{u}}\| \|\vec{\mathbf{v}}\|}
\right)
$$

### Resulting Summary Sent to LLM

> User performed 6 reps of pull-ups. Reps 1-4 achieved full range of
> motion. Reps 5-6 failed to bring the chin past the bar plane
> (incomplete shoulder extension). No critical spinal or hip sagging
> detected.

## 4. Development Tech Stack (Zero/Low Cost First)

- **Frontend Tracker:** MediaPipe Pose API (free, runs natively on client
  browsers/devices).
- **Heuristics Engine:** Python (NumPy/SciPy) or a TypeScript serverless
  function.
- **Cognitive Playground:** Local open-weights execution during development
  (Llama 3/4 variants), migrating to low-tier developer endpoints for
  Gemini/GPT models during integration testing.
