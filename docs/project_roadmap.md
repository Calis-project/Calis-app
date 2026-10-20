\# Calis-App Macro Roadmap \& Strategic Milestones



This document outlines the high-level trajectory, architectural evolution, and milestone planning for \*\*Calis-App\*\* from initial proof-of-concept to production release.



\---



\## 🗺️ Project Trajectory Overview



\[Sprint 01: POC]          \[Sprint 02: Edge Pipeline]       \[Sprint 03: Live UX \& Feedback]



Golden Spike (80%)      - CameraX Zero-Copy (28 FPS)      - E2E Live Workout Loop



Python Rule Engine      - PushupEvaluator (90%)           - Real-time Audio/Haptics



Dataset \& Annotations   - 6-Joint Dynamic Skeleton        - Physical Device Field Test

│                               │                               │

└───────────────────────────────┴───────────────────────────────┘

│

▼

\[Sprint 04: Analytics \& Expansion] ──► \[Sprint 05: Hardening \& Release] ──► \[v1.0 Store Launch]



Local SQLite History                 - Multi-Condition Robustness



Rep Breakdown \& Form Score           - APK/Bundle Size Optimization



Exercise #2 (Squats / Pull-ups)      - Google Play Internal Testing





\---



\## 📊 Sprint Matrix \& Milestone Planning



| Sprint | Timeline | Key Milestone | Core Deliverables | Exit Criteria (DoD) | Status |

| :--- | :--- | :--- | :--- | :--- | :--- |

| \*\*Sprint 01\*\* | Sep 2026 | Golden Spike POC | Offline landmark extraction, baseline biomechanics rules, initial reference dataset | Accuracy $\\ge 80\\%$ on reference videos, processing time $<20\\text{ ms}$ | \*\*Completed\*\* |

| \*\*Sprint 02\*\* | Oct 1–18, 2026 | Flutter Edge Integration | Native CameraX pipeline\[cite: 1], `PushupEvaluator` class\[cite: 5], 6-joint skeletal rendering | $\\ge 25\\text{ FPS}$\[cite: 1], latency $<35\\text{ ms}$\[cite: 1], accuracy $\\ge 90\\%$\[cite: 5] | \*\*Closing (85%)\*\*\[cite: 5] |

| \*\*Sprint 03\*\* | Oct 19 - Nov 1, 2026 | Interactive Live Workout | Connect landmark stream to evaluation engine in Flutter, audio/haptic feedback on errors/reps, HUD counter | 10-minute continuous workout execution without memory leaks or crashes | Upcoming |

| \*\*Sprint 04\*\* | Nov 2–15, 2026 | Analytics \& Multi-Exercise | Local offline SQLite DB, error logging/records, exercise #2 module (Squats) | Offline session persistence, $\\ge 85\\%$ accuracy on secondary exercise | Planned |

| \*\*Sprint 05\*\* | Nov 16–29, 2026 | Production Hardening | Binary optimization (APK Size $<40\\text{MB}$), low-light/angle robustness testing, internal release | 99.5% crash-free rate, thermal stability (no thermal throttling under load) | Planned |



\---



\## 🔍 Detailed Milestone Breakdown



\### Sprint 03: Interactive Live Workout Loop

\* \*\*Core Objective:\*\* Enable users to place their phone on the floor, start a workout, and perform push-ups without constantly staring at the screen, guided purely by audio beeps (rep confirmation) and voice cues (form corrections like `HIP\_SAG`)\[cite: 5].

\* \*\*Key Tasks:\*\*

&#x20; \* Connect `pose\_landmark\_bridge.dart` directly to a Dart port/instance of `PushupEvaluator` for real-time edge processing\[cite: 5].

&#x20; \* Integrate audio cues and haptic feedback triggers.

&#x20; \* Field test on physical devices for battery consumption and thermal limits.



\### Sprint 04: Local Analytics \& Exercise Expansion

\* \*\*Core Objective:\*\* Store workout achievements 100% offline (ensuring privacy) and prove the modular scalability of the biomechanics engine to other calisthenics exercises.

\* \*\*Key Tasks:\*\*

&#x20; \* Design local SQLite/Isar schemas for rep history, error breakdowns, and session timestamps.

&#x20; \* Develop `squat\_rules.py` (analyzing knee depth, hip angle, and spinal alignment).

&#x20; \* Collect reference benchmark datasets for secondary movements.



\### Sprint 05: Production Hardening \& Store Launch

\* \*\*Core Objective:\*\* Deliver an MVP v1.0 release candidate to testers via Google Play Console (Closed Testing) and handle adverse lighting/angle environments.

\* \*\*Key Tasks:\*\*

&#x20; \* Apply insights from low-light and 45-degree angle datasets to refine angle thresholds.

&#x20; \* Shrink binary footprints (ProGuard/R8, stripping unnecessary MediaPipe assets).

&#x20; \* Conduct stability audits and compile official MVP readiness reports.



\---



\## 🛡️ Top 3 Technical Risks \& Mitigations



1\. \*\*Thermal Throttling \& Battery Drain:\*\* Running continuous CameraX feeds, 28 FPS AI inference\[cite: 1], and canvas rendering can heat up devices during long sessions.

&#x20;  \* \*Mitigation:\* Implement dynamic frame-dropping if device temperature/battery warnings trigger.

2\. \*\*Real-world Perspective Variations:\*\* Users do not always position cameras at precise 90-degree lateral angles.

&#x20;  \* \*Mitigation:\* Incorporate multi-angle dataset tolerances into the `calculate\_angle` normalization formula\[cite: 5].

3\. \*\*Biomechanics Logic Parity:\*\* Keeping Python evaluation rules aligned with Flutter/Dart execution.

&#x20;  \* \*Mitigation:\* Clean, modular porting of evaluation rules directly into Dart for edge parity.

