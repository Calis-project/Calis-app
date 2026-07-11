"use client";

import { useEffect, useRef, useState, type RefObject } from "react";

import { EXERCISES, type ExerciseId } from "@/lib/cv/exercises";
import { drawPose } from "@/lib/cv/drawPose";
import { getPoseLandmarker } from "@/lib/cv/poseEngine";
import { RepCounter, type CvEvent, type CvSnapshot } from "@/lib/cv/repCounter";
import type { LandmarkPoint } from "@/lib/cv/poseMath";

const DETECT_INTERVAL_MS = 33;
const SNAPSHOT_INTERVAL_MS = 100;

type PoseTrackingOptions = {
  videoRef: RefObject<HTMLVideoElement | null>;
  canvasRef: RefObject<HTMLCanvasElement | null>;
  enabled: boolean;
  exercise: ExerciseId;
  isLive: boolean;
  onEvent?: (event: CvEvent) => void;
  // Change this value (e.g. new video source) to reset the rep counter.
  resetKey?: unknown;
};

export function usePoseTracking({
  videoRef,
  canvasRef,
  enabled,
  exercise,
  isLive,
  onEvent,
  resetKey,
}: PoseTrackingOptions) {
  const [snapshot, setSnapshot] = useState<CvSnapshot>();
  const [cvReady, setCvReady] = useState(false);
  const [cvError, setCvError] = useState<string>();

  const counterRef = useRef<RepCounter>(null);
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  });

  useEffect(() => {
    if (!enabled) {
      return;
    }

    counterRef.current = new RepCounter(EXERCISES[exercise]);

    let cancelled = false;
    let rafId = 0;
    let lastDetectMs = 0;
    let lastSnapshotMs = 0;

    async function run() {
      let landmarker;
      try {
        landmarker = await getPoseLandmarker();
      } catch (error) {
        if (!cancelled) {
          setCvError(
            error instanceof Error
              ? `Pose model failed to load: ${error.message}`
              : "Pose model failed to load.",
          );
        }
        return;
      }

      if (cancelled) {
        return;
      }
      setCvReady(true);
      setCvError(undefined);
      setSnapshot(undefined);

      const loop = () => {
        if (cancelled) {
          return;
        }
        rafId = requestAnimationFrame(loop);

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const counter = counterRef.current;
        if (!video || !canvas || !counter || video.readyState < 2) {
          return;
        }

        const now = performance.now();
        if (now - lastDetectMs < DETECT_INTERVAL_MS) {
          return;
        }
        lastDetectMs = now;

        if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
        }

        // detectForVideo needs monotonically increasing timestamps, so we use
        // wall-clock time rather than video.currentTime (scrubbing goes backwards).
        const result = landmarker.detectForVideo(video, now);
        const landmarks = result.landmarks?.[0] as LandmarkPoint[] | undefined;

        const ctx = canvas.getContext("2d");
        if (ctx) {
          drawPose(ctx, landmarks, canvas.width, canvas.height);
        }

        if (!landmarks) {
          return;
        }

        // Only advance rep state while the footage moves forward in real time;
        // scrubbing a paused video updates the readout without corrupting reps.
        const counting = isLive || (!video.paused && !video.ended);
        const next = counting
          ? counter.update(landmarks, now)
          : { snapshot: counter.preview(landmarks), events: [] };

        for (const event of next.events) {
          onEventRef.current?.(event);
        }

        if (next.events.length || now - lastSnapshotMs >= SNAPSHOT_INTERVAL_MS) {
          lastSnapshotMs = now;
          setSnapshot(next.snapshot);
        }
      };

      rafId = requestAnimationFrame(loop);
    }

    run();

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafId);
    };
  }, [enabled, isLive, exercise, resetKey, videoRef, canvasRef]);

  return { snapshot, cvReady, cvError };
}
