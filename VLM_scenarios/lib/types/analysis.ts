export type AnalysisMode = "frames" | "video" | "hybrid";

export type TokenUsage = {
  promptTokens: number;
  outputTokens: number;
  totalTokens: number;
};

export type AnalyzeSuccess = {
  ok: true;
  mode: AnalysisMode;
  model: string;
  text: string;
  timingMs: number;
  usage?: TokenUsage;
  // Rough paid-tier USD cost for this call (undefined on the free tier when
  // no usage metadata is returned). See lib/ai/pricing.ts.
  estCostUsd?: number;
};

export type AnalyzeFailure = {
  ok: false;
  error: {
    code: string;
    message: string;
  };
};

export type AnalyzeResponse = AnalyzeSuccess | AnalyzeFailure;

export type HealthResponse = {
  ok: true;
  model: string;
  hasKey: boolean;
};

export type FrameInput = {
  data: string;
  mimeType: "image/jpeg" | "image/png" | "image/webp";
};

// Set-level summary produced by the on-device rep counter and sent to Gemini.
export type CvSetSummary = {
  exercise: string;
  reps: number;
  formScores: number[];
  avgKeyAngleDeg: number;
  keyJoint: string;
  rangeOfMotionDeg: number;
  bodyLine: string;
  tempo: string;
  weakPoints: string[];
};

export type FramesAnalyzeRequest = {
  prompt: string;
  frames: FrameInput[];
};

export type HybridAnalyzeRequest = {
  prompt: string;
  frames: FrameInput[];
  cvData: CvSetSummary;
};
