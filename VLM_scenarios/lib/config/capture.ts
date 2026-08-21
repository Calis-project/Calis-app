// Client-safe capture / analysis levers.
//
// The single biggest free-tier cost lever is how many frames each Gemini call
// carries and how large each frame is: image tokens ≈ frames × ~258 (a 768px
// tile). Fewer, smaller frames = proportionally cheaper calls. Tune here.

export const CAPTURE_MAX_WIDTH = 512; // was 640 — smaller frames, fewer image tokens
export const CAPTURE_JPEG_QUALITY = 0.65;

// Frames sent on a per-trigger hybrid/VLM call (set-end, form-drop, ask-coach).
export const FRAMES_PER_CALL = 2; // was 3

// Frames sent on a single batched end-of-workout call — one representative
// keyframe per recent set.
export const BATCH_MAX_FRAMES = 4;
