import "server-only";

import {
  FileState,
  GoogleGenAI,
  type Part,
  type File as GeminiFile,
} from "@google/genai";

import { getGeminiApiKey, getGeminiModel, hasGeminiApiKey } from "@/lib/ai/config";
import { ApiError, toErrorMessage } from "@/lib/ai/errors";
import { estimateCostUsd } from "@/lib/ai/pricing";
import type { AnalysisMode, TokenUsage } from "@/lib/types/analysis";
import type { GeminiPart } from "@/lib/types/gemini";
import type { GenerateContentResponse } from "@google/genai";

const MAX_FILE_BYTES = 100 * 1024 * 1024;
const FILE_POLL_INTERVAL_MS = 1_000;
const FILE_POLL_TIMEOUT_MS = 45_000;

function getClient() {
  if (!hasGeminiApiKey()) {
    throw new ApiError(
      500,
      "missing_gemini_key",
      "Missing GEMINI_API_KEY in .env.local.",
    );
  }

  return new GoogleGenAI({
    apiKey: getGeminiApiKey(),
  });
}

function toSdkParts(parts: GeminiPart[]): Part[] {
  return parts.map((part) => {
    if ("text" in part) {
      return { text: part.text };
    }

    if ("inlineData" in part) {
      return {
        inlineData: {
          data: part.inlineData.data,
          mimeType: part.inlineData.mimeType,
        },
      };
    }

    return {
      fileData: {
        fileUri: part.fileData.fileUri,
        mimeType: part.fileData.mimeType,
      },
    };
  });
}

function assertUsableFile(file: File, acceptedPrefix: "image/" | "video/") {
  if (!file.size) {
    throw new ApiError(400, "empty_file", "Upload a non-empty file.");
  }

  if (file.size > MAX_FILE_BYTES) {
    throw new ApiError(
      400,
      "file_too_large",
      "The uploaded file is too large for this demo. Use a file under 100 MB.",
    );
  }

  if (!file.type.startsWith(acceptedPrefix)) {
    throw new ApiError(
      400,
      "unsupported_file_type",
      `Upload a ${acceptedPrefix === "image/" ? "image" : "video"} file.`,
    );
  }
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function toTokenUsage(
  metadata: GenerateContentResponse["usageMetadata"],
): TokenUsage | undefined {
  if (!metadata) {
    return undefined;
  }

  return {
    promptTokens: metadata.promptTokenCount ?? 0,
    outputTokens: metadata.candidatesTokenCount ?? 0,
    totalTokens: metadata.totalTokenCount ?? 0,
  };
}

async function waitForActiveFile(ai: GoogleGenAI, file: GeminiFile) {
  if (!file.name) {
    throw new ApiError(500, "file_upload_failed", "Gemini did not return a file name.");
  }

  const started = Date.now();
  let current = file;

  while (current.state === FileState.PROCESSING) {
    if (Date.now() - started > FILE_POLL_TIMEOUT_MS) {
      throw new ApiError(
        504,
        "file_processing_timeout",
        "Gemini is still processing the uploaded video. Try a shorter clip.",
      );
    }

    await delay(FILE_POLL_INTERVAL_MS);
    current = await ai.files.get({ name: file.name });
  }

  if (current.state === FileState.FAILED) {
    throw new ApiError(
      502,
      "file_processing_failed",
      current.error?.message || "Gemini could not process the uploaded file.",
    );
  }

  return current;
}

export async function generateGeminiAnalysis(mode: AnalysisMode, parts: GeminiPart[]) {
  const ai = getClient();
  const model = getGeminiModel();
  const started = Date.now();

  try {
    const response = await ai.models.generateContent({
      model,
      contents: [
        {
          role: "user",
          parts: toSdkParts(parts),
        },
      ],
    });

    const usage = toTokenUsage(response.usageMetadata);
    return {
      ok: true as const,
      mode,
      model,
      text: response.text || "No response text returned by Gemini.",
      timingMs: Date.now() - started,
      usage,
      estCostUsd: estimateCostUsd(model, usage),
    };
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw new ApiError(502, "gemini_request_failed", toErrorMessage(error));
  }
}

export async function generateFromUploadedFile(
  mode: "video",
  file: File,
  prompt: string,
) {
  assertUsableFile(file, "video/");

  const ai = getClient();
  const model = getGeminiModel();
  const started = Date.now();

  try {
    const uploaded = await ai.files.upload({
      file,
      config: {
        mimeType: file.type,
        displayName: file.name,
      },
    });
    const usableFile = await waitForActiveFile(ai, uploaded);

    if (!usableFile.uri || !usableFile.mimeType) {
      throw new ApiError(
        500,
        "file_upload_failed",
        "Gemini did not return usable uploaded file metadata.",
      );
    }

    const response = await ai.models.generateContent({
      model,
      contents: [
        {
          role: "user",
          parts: [
            { text: prompt },
            {
              fileData: {
                fileUri: usableFile.uri,
                mimeType: usableFile.mimeType,
              },
            },
          ],
        },
      ],
    });

    const usage = toTokenUsage(response.usageMetadata);
    return {
      ok: true as const,
      mode,
      model,
      text: response.text || "No response text returned by Gemini.",
      timingMs: Date.now() - started,
      usage,
      estCostUsd: estimateCostUsd(model, usage),
    };
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw new ApiError(502, "gemini_request_failed", toErrorMessage(error));
  }
}
