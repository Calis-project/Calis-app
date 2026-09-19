# Calis App (Sprint 01: Golden Spike)

AI-driven Calisthenics Form Analysis & Real-time Pose Correction.

## Architecture
- **Client:** Flutter (Mobile-First, Edge Inference)
- **Vision:** MediaPipe Pose (<35ms latency on CPU)
- **Biomechanics:** Kinematic Joint Angle Evaluation (Push-up)

## Repository Structure
- `docs/`: System documentation per project class
- `dataset/raw/`: Golden spike benchmark clips
- `mobile/`: Flutter client application
- `src/`: Core Python vision & biomechanics modules
- `tests/`: Automated end-to-end integration tests
