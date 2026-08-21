import {
  assertContentLength,
  assertPrompt,
  fail,
  JSON_BODY_LIMIT_BYTES,
  ok,
  readJsonBody,
} from "@/lib/api/http";
import { assertFrames } from "@/lib/api/validators";
import { generateGeminiAnalysis } from "@/lib/ai/gemini";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    assertContentLength(request, JSON_BODY_LIMIT_BYTES);
    const payload = await readJsonBody<{
      prompt?: unknown;
      frames?: unknown;
    }>(request);
    const prompt = assertPrompt(payload.prompt);
    const frames = assertFrames(payload.frames);

    const result = await generateGeminiAnalysis("frames", [
      { text: prompt },
      ...frames.map((frame) => ({
        inlineData: {
          data: frame.data,
          mimeType: frame.mimeType,
        },
      })),
    ]);

    return ok(result);
  } catch (error) {
    return fail(error);
  }
}
