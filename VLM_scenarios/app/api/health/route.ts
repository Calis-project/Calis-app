import { NextResponse } from "next/server";

import { getGeminiModel, hasGeminiApiKey } from "@/lib/ai/config";
import type { HealthResponse } from "@/lib/types/analysis";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const payload: HealthResponse = {
    ok: true,
    model: getGeminiModel(),
    hasKey: hasGeminiApiKey(),
  };

  return NextResponse.json(payload);
}
