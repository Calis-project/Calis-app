"use client";

import { FilesetResolver, PoseLandmarker } from "@mediapipe/tasks-vision";

const WASM_URL =
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm";
const MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task";

let landmarkerPromise: Promise<PoseLandmarker> | undefined;

export function getPoseLandmarker() {
  if (!landmarkerPromise) {
    landmarkerPromise = (async () => {
      const vision = await FilesetResolver.forVisionTasks(WASM_URL);
      return PoseLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: MODEL_URL,
          delegate: "GPU",
        },
        runningMode: "VIDEO",
        numPoses: 1,
      });
    })().catch((error) => {
      // Allow a retry on the next call instead of caching the failure forever.
      landmarkerPromise = undefined;
      throw error;
    });
  }

  return landmarkerPromise;
}
