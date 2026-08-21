"use client";

import { CAPTURE_JPEG_QUALITY, CAPTURE_MAX_WIDTH } from "@/lib/config/capture";
import type { FrameInput } from "@/lib/types/analysis";

// Grabs the current video frame as a base64 JPEG sized for Gemini.
export function captureFrame(video: HTMLVideoElement): FrameInput | undefined {
  if (!video.videoWidth || !video.videoHeight || video.readyState < 2) {
    return undefined;
  }

  const scale = Math.min(1, CAPTURE_MAX_WIDTH / video.videoWidth);
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(video.videoWidth * scale);
  canvas.height = Math.round(video.videoHeight * scale);

  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return undefined;
  }

  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const dataUrl = canvas.toDataURL("image/jpeg", CAPTURE_JPEG_QUALITY);
  const base64 = dataUrl.split(",")[1];

  if (!base64) {
    return undefined;
  }

  return { data: base64, mimeType: "image/jpeg" };
}
