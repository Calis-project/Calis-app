# Calis-App: Product & Engineering Roadmap

## Vision Statement
An on-device, privacy-first AI calisthenics coach providing real-time biomechanical feedback with zero server latency and zero cloud costs.

---

## Release Phases

### Phase 1: Golden Spike POC (Current — Sprint 01)
- **Goal:** Validate core AI accuracy on push-up form using sagittal video benchmarks.
- **DoD:** $\ge 80\%$ classification accuracy between valid reps and `HIP_SAG`.
- **Deliverables:** MediaPipe extraction pipeline, kinematics rules engine, Golden Spike test harness.

### Phase 2: Real-time Edge Integration (Sprint 02)
- **Goal:** Bridge the Python/MediaPipe inference logic into the Flutter mobile client.
- **Deliverables:** Camera stream preview, real-time skeleton overlay, on-screen audio/visual cue triggers.

### Phase 3: MVP Release (Sprint 03)
- **Goal:** Standalone offline mobile app tracking complete push-up sets.
- **Deliverables:** Session summary screen, rep counter state machine, local SQLite/Hive persistence.

### Phase 4: Calisthenics Expansion (Sprint 04+)
- **Goal:** Support multi-exercise detection.
- **Deliverables:** Pull-up form validation (frontal view), Bodyweight Squats, and progression tracking.
