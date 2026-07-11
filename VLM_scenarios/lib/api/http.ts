import { NextResponse } from "next/server";

import { ApiError, toErrorMessage } from "@/lib/ai/errors";
import type { AnalyzeFailure, AnalyzeSuccess } from "@/lib/types/analysis";

export const JSON_BODY_LIMIT_BYTES = 20 * 1024 * 1024;
export const FILE_BODY_LIMIT_BYTES = 100 * 1024 * 1024;

export function assertContentLength(request: Request, limitBytes: number) {
  const contentLength = request.headers.get("content-length");

  if (!contentLength) {
    return;
  }

  const bytes = Number(contentLength);

  if (Number.isFinite(bytes) && bytes > limitBytes) {
    throw new ApiError(
      400,
      "request_too_large",
      "The request is too large for this demo.",
    );
  }
}

export function ok(payload: AnalyzeSuccess) {
  return NextResponse.json(payload);
}

export function fail(error: unknown) {
  const status = error instanceof ApiError ? error.status : 500;
  const code = error instanceof ApiError ? error.code : "unexpected_error";
  const message = error instanceof ApiError ? error.message : toErrorMessage(error);

  const payload: AnalyzeFailure = {
    ok: false,
    error: {
      code,
      message,
    },
  };

  return NextResponse.json(payload, { status });
}

export function assertPrompt(prompt: unknown) {
  if (typeof prompt !== "string" || !prompt.trim()) {
    throw new ApiError(400, "empty_prompt", "Provide a non-empty prompt.");
  }

  return prompt.trim();
}

export async function readJsonBody<T>(request: Request) {
  try {
    return (await request.json()) as T;
  } catch {
    throw new ApiError(400, "invalid_json", "Request body must be valid JSON.");
  }
}
