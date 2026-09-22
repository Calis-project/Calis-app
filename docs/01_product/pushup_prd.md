# Product Requirements Document (PRD): Push-Up Form Tracking & Pose Constraints

- **Document ID:** PRD-EX-001
- **Feature:** Push-Up Form Correction & Repetition Counting
- **Sprint:** Sprint 01
- **Target File:** `docs/01_product/pushup_prd.md`
- **Vision Engine:** MediaPipe Pose Landmark Detection (33 3D Landmarks)
- **Status:** Approved / Ready for Implementation

---

## 1. Objective & Scope

This document specifies the physical camera setup parameters, geometric validation rules, and the complete end-to-end user experience (UX) flow for tracking push-ups in the Calisthenics App.

The system uses MediaPipe Pose 3D landmarks to:
1. Validate user positioning and environmental constraints.
2. Measure joint angles and detect spinal/hip breaks in real time.
3. Provide synchronous audiovisual corrective cues.
4. Count and log valid, full-range repetitions.

---

## 2. Geometric & Physical Camera Constraints

To achieve consistent tracking confidence, eliminate joint occlusion, and minimize 2D-to-3D projection distortion, device placement must adhere to the parameters below.

| Parameter | Optimal Value | Tolerable Range | Technical Rationale |
| :--- | :--- | :--- | :--- |
| **Camera View Angle** | $90^\circ$ relative to body axis (Pure Sagittal Plane / Lateral view) | $80^\circ - 100^\circ$ | Provides an unobstructed view of the shoulder, elbow, wrist, hip, knee, and ankle joints while eliminating foreshortening. |
| **Distance to User** | $2.2\text{ m}$ | $2.0 - 2.5\text{ m}$ | Keeps the full body (from crown of head to toes) in frame during both the top lockout and bottom positions without edge clipping. |
| **Camera Height** | $40\text{ cm}$ above floor level | $30 - 50\text{ cm}$ | Aligns the lens with the median horizontal plane of a user in a plank position, minimizing pitch-angle parallax. |
| **Camera Tilt (Pitch/Roll)**| $0^\circ$ (Perpendicular to floor plane) | $\pm 5^\circ$ | Prevents artificial skew in trunk angle and hip elevation calculations. |
| **Ambient Illumination** | $\ge 300\text{ Lux}$ | High subject-to-floor contrast | Minimizes landmark jitter; avoids backlighting where user silhouette loses joint clarity. |

### 2.1 MediaPipe Landmark Mapping

The tracking engine monitors the following key landmark indices:
- **Upper Body (Push Mechanics):**
  - Shoulder: `LEFT_SHOULDER` (`11`) or `RIGHT_SHOULDER` (`12`)
  - Elbow: `LEFT_ELBOW` (`13`) or `RIGHT_ELBOW` (`14`)
  - Wrist: `LEFT_WRIST` (`15`) or `RIGHT_WRIST` (`16`)
- **Core & Lower Body (Alignment):**
  - Hip: `LEFT_HIP` (`23`) or `RIGHT_HIP` (`24`)
  - Knee: `LEFT_KNEE` (`25`) or `RIGHT_KNEE` (`26`)
  - Ankle: `LEFT_ANKLE` (`27`) or `RIGHT_ANKLE` (`28`)

*Note: The engine tracks the side facing the camera based on visibility scores (`visibility > 0.7`).*

---

## 3. Mathematical & Algorithmic State Logic

### 3.1 Angle Calculations
Angles are calculated as vector angles between normalized 3D landmark points:

1. **Elbow Angle ($\theta_{\text{elbow}}$):**  
   Computed between `SHOULDER` $\rightarrow$ `ELBOW` and `ELBOW` $\rightarrow$ `WRIST`.
   - **Plank / Lockout:** $\theta_{\text{elbow}} \ge 160^\circ$
   - **Target Bottom Depth:** $\theta_{\text{elbow}} \le 90^\circ$

2. **Body Alignment Angle ($\theta_{\text{hip}}$):**  
   Computed between `SHOULDER` $\rightarrow$ `HIP` and `HIP` $\rightarrow$ `ANKLE` (or `KNEE`).
   - **Valid Alignment:** $165^\circ \le \theta_{\text{hip}} \le 180^\circ$
   - **Sagging Hips (Hyperextension):** $\theta_{\text{hip}} < 160^\circ$
   - **Piking Hips (Pelvic Elevation):** $\theta_{\text{hip}} > 195^\circ$

---

## 4. End-to-End User Experience (UX Flow)

[Phase 1: Setup & Framing] ──> [Phase 2: Plank Lock-in] ──> [Phase 3: Active Repetition] ──> [Phase 4: Rep Count / Exit]
│                               │                               │                                │
▼                               ▼                               ▼                                ▼
Guide Bounding Box              Hold for 1.0 sec                Descent & Bottom Check           Increment & Log


### Phase 1: Setup & Calibration
- User sets device on a stand or stable surface at $\approx 40\text{ cm}$ height, $2.0 - 2.5\text{ m}$ away.
- Screen displays a lateral silhouette guideline.
- Dynamic prompts:
  - If joints are cut off: *"Step back to fit your full body in frame."*
  - If facing front: *"Turn sideways (90° lateral view)."*
  - When framing is satisfied: Silhouette highlights green with audio: *"Get into plank position."*

### Phase 2: Plank Stabilization (Lock-in)
- User enters the top push-up position (arms extended, straight line).
- State engine confirms:
  - $\theta_{\text{elbow}} \ge 160^\circ$
  - $165^\circ \le \theta_{\text{hip}} \le 180^\circ$
- The user must hold this stable state for **1.0 continuous second**.
- System plays a chime and transitions state to `TRACKING_ACTIVE`.

### Phase 3: Active Repetition & Real-Time Correction
- **Descent Phase:**
  - As $\theta_{\text{elbow}}$ reduces from $160^\circ$ toward $90^\circ$, alignment is monitored continuously.
  - If $\theta_{\text{hip}} < 160^\circ$: Prompt: *"Engage your core, don't sag your hips."*
  - If $\theta_{\text{hip}} > 195^\circ$: Prompt: *"Keep your hips down, body straight."*
- **Bottom Inflection Point:**
  - When $\theta_{\text{elbow}} \le 90^\circ$: The internal flag `depth_achieved` is set to `true`.
  - If the user ascends early ($\theta_{\text{elbow}} > 90^\circ$): Prompt: *"Go lower for full range."*
- **Ascent Phase:**
  - User returns upward toward starting plank position while maintaining $165^\circ \le \theta_{\text{hip}} \le 180^\circ$.

### Phase 4: Repetition Completion & Session Termination
- **Valid Rep:**
  - $\theta_{\text{elbow}}$ reaches $\ge 160^\circ$ AND `depth_achieved == true` without breaking trunk alignment.
  - Increment count by `+1`.
  - Play confirmation sound (or haptic tap) and announce number.
  - Reset state flags for the next cycle.
- **Session End:**
  - If the user leaves the frame or rests on the ground for $> 3\text{ seconds}$, tracking auto-pauses/ends.
  - Display summary screen: Total completed reps, form adherence rate, and recurring errors.

---

## 5. Corrective Feedback Catalog

| Condition | Metric / Trigger | Audio Cue | Visual Badge / Banner |
| :--- | :--- | :--- | :--- |
| **Incomplete Depth** | Ascent triggered while $\theta_{\text{elbow}} > 90^\circ$ | *"Go lower"* | Amber warning: `Insufficient Depth` |
| **Sagging Hips** | $\theta_{\text{hip}} < 160^\circ$ during any phase | *"Core tight, lift hips"* | Red banner: `Sagging Spine` |
| **Piked Hips** | $\theta_{\text{hip}} > 195^\circ$ during any phase | *"Lower your hips"* | Red banner: `Hips Too High` |
| **Partial Lockout** | Descent restarted while $\theta_{\text{elbow}} < 160^\circ$ | *"Lock arms at the top"* | Blue notice: `Reset to Top` |
| **Occlusion / Exit** | Landmark visibility $< 0.65$ on key joints | *"Move back into camera view"* | Gray overlay: `Subject Lost` |

---

## 6. Definition of Done (DoD) & Acceptance Criteria

- [ ] Camera placement parameters ($2.0 - 2.5\text{ m}$ distance, $40\text{ cm}$ elevation, $90^\circ$ sagittal view) reviewed and approved without ambiguity.
- [ ] Landmark mapping and 3D angle definitions ($\theta_{\text{elbow}}$, $\theta_{\text{hip}}$) finalized for vision team implementation.
- [ ] Real-time feedback triggers and UX state machine comprehensively mapped.
- [ ] Markdown file committed to repository at `docs/01_product/pushup_prd.md`.

