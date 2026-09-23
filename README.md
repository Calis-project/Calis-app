# Calis-App: On-Device AI Calisthenics Coach

An edge-first, privacy-focused mobile application built with **Flutter** and **MediaPipe** providing real-time biomechanical form analysis and corrective audio/visual cues for calisthenics exercises.

---

## Architecture & Core Tech Stack

- **Client:** Flutter (Dart) — High-FPS camera preview, on-screen skeletal overlay, state-driven UI cues.
- **Vision Engine:** MediaPipe Pose Landmark Detection — Executed purely on-device (Zero cloud streaming, Zero GPU hosting costs).
- **Biomechanics Engine:** Deterministic 2D/3D Kinematic Rule Engine calculating joint angles, phase states, and form deviations (e.g., `HIP_SAG`, `NO_REP_DEPTH`).
- **Data Privacy:** Video frames are analyzed transiently in device RAM and instantly discarded (GDPR-compliant by design).

---

## Project Status: Sprint 01 Complete (Golden Spike POC)

- **Benchmark Accuracy:** Achieved **80.0%** classification accuracy on reference sagittal push-up dataset.
- **Inference Latency:** ~14 ms/frame on standard CPU (capable of 70+ FPS).
- **Next Milestone:** Sprint 02 — Flutter Camera Integration & On-Device Dart/C++ Bridge.

---

## Documentation Navigation

Detailed engineering and product documentation can be found in the `docs/` directory:
- `docs/01_product/pushup_prd.md` — Push-up biomechanical criteria and user flows.
- `docs/02_vision/ROADMAP.md` — Multi-phase product roadmap.
- `docs/07_architecture/golden_spike_report.md` — Benchmark report and latency analysis.
- `docs/07_architecture/sprint_01_state.yaml` — Real-time machine-readable sprint registry.
