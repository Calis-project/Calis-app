import { assertContentLength, assertPrompt, fail, FILE_BODY_LIMIT_BYTES, ok } from "@/lib/api/http";
import { assertUploadedFile } from "@/lib/api/validators";
import { generateFromUploadedFile } from "@/lib/ai/gemini";
import { defaultVlmPrompt } from "@/lib/ai/prompts";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    assertContentLength(request, FILE_BODY_LIMIT_BYTES);
    const formData = await request.formData();
    const file = assertUploadedFile(formData.get("file"));
    const prompt = assertPrompt(formData.get("prompt") || defaultVlmPrompt);

    const result = await generateFromUploadedFile("video", file, prompt);
    return ok(result);
  } catch (error) {
    return fail(error);
  }
}
