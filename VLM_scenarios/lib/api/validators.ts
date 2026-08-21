import { ApiError } from "@/lib/ai/errors";
import type { CvSetSummary, FrameInput } from "@/lib/types/analysis";

const MAX_FRAMES = 10;
const MAX_BASE64_CHARS_PER_FRAME = 5 * 1024 * 1024;
const IMAGE_MIME_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNumberArray(value: unknown): value is number[] {
  return Array.isArray(value) && value.every((item) => typeof item === "number");
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

export function assertFrames(value: unknown): FrameInput[] {
  if (!Array.isArray(value) || !value.length) {
    throw new ApiError(400, "empty_frames", "Provide at least one extracted frame.");
  }

  if (value.length > MAX_FRAMES) {
    throw new ApiError(400, "too_many_frames", `Use ${MAX_FRAMES} frames or fewer.`);
  }

  return value.map((frame, index) => {
    if (!isRecord(frame)) {
      throw new ApiError(400, "invalid_frame", `Frame ${index + 1} is invalid.`);
    }

    const data = frame.data;
    const mimeType = frame.mimeType;

    if (typeof data !== "string" || !data.trim()) {
      throw new ApiError(400, "invalid_frame", `Frame ${index + 1} is empty.`);
    }

    if (data.length > MAX_BASE64_CHARS_PER_FRAME) {
      throw new ApiError(
        400,
        "frame_too_large",
        `Frame ${index + 1} is too large for this demo.`,
      );
    }

    if (typeof mimeType !== "string" || !IMAGE_MIME_TYPES.has(mimeType)) {
      throw new ApiError(
        400,
        "unsupported_frame_type",
        `Frame ${index + 1} must be JPEG, PNG, or WebP.`,
      );
    }

    return {
      data,
      mimeType: mimeType as FrameInput["mimeType"],
    };
  });
}

export function assertCvSummary(value: unknown): CvSetSummary {
  if (!isRecord(value)) {
    throw new ApiError(400, "invalid_cv_data", "Provide CV set summary data.");
  }

  const {
    exercise,
    reps,
    formScores,
    avgKeyAngleDeg,
    keyJoint,
    rangeOfMotionDeg,
    bodyLine,
    tempo,
    weakPoints,
  } = value;

  if (
    typeof exercise !== "string" ||
    typeof reps !== "number" ||
    !isNumberArray(formScores) ||
    typeof avgKeyAngleDeg !== "number" ||
    typeof keyJoint !== "string" ||
    typeof rangeOfMotionDeg !== "number" ||
    typeof bodyLine !== "string" ||
    typeof tempo !== "string" ||
    !isStringArray(weakPoints)
  ) {
    throw new ApiError(
      400,
      "invalid_cv_data",
      "CV summary is missing required movement fields.",
    );
  }

  return {
    exercise,
    reps,
    formScores,
    avgKeyAngleDeg,
    keyJoint,
    rangeOfMotionDeg,
    bodyLine,
    tempo,
    weakPoints,
  };
}

export function assertUploadedFile(value: FormDataEntryValue | null) {
  if (!(value instanceof File)) {
    throw new ApiError(400, "missing_file", "Upload a file.");
  }

  return value;
}
