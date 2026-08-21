import type { CvSetSummary } from "@/lib/types/analysis";

export const defaultVlmPrompt = `You are an expert calisthenics coach analyzing exercise footage.

Identify the exercise, describe visible form quality, flag risks, and give 2-3 practical cues. Be concise and specific to what you can actually see.`;

// Appended automatically when a full video (not a snapshot) is analyzed.
export const videoTimingInstruction = `The input is a full video. Whenever you flag a form risk, fault, or notable moment, cite the timestamp where it happens in M:SS format (e.g. "at 0:14"). If a fault repeats, give the timestamp of the first occurrence and of the worst occurrence.`;

export const defaultHybridPrompt = `You are a calisthenics coach combining on-device pose-tracking data with visual keyframes.

Use the structured CV data for measurable trends and the frames for visible form context. Explain where they agree, where visual inspection adds nuance, and give clear next-set advice. Be concise.`;

// Sent once at the end of a whole workout (batched mode) — one Gemini call
// reviewing every set instead of one call per set. Cheapest coaching tier.
export const defaultBatchedPrompt = `You are a calisthenics coach reviewing a whole training session at once.

You are given the per-set on-device CV data for the full session plus a few representative keyframes. Summarize how the session went overall, call out the 1-2 sets where form broke down most, note fatigue or progression trends across sets, and give 2-3 concrete priorities for next session. Be concise.`;

export function cvSummaryToPrompt(summary: CvSetSummary) {
  return `Structured CV data (on-device pose tracking):
- Exercise: ${summary.exercise}
- Reps: ${summary.reps}
- Form scores per rep: ${summary.formScores.join(", ") || "none"}
- Average ${summary.keyJoint} angle at rep peak: ${summary.avgKeyAngleDeg} degrees
- Observed range of motion: ${summary.rangeOfMotionDeg} degrees
- Body line: ${summary.bodyLine}
- Tempo: ${summary.tempo}
- Weak points: ${summary.weakPoints.join(", ") || "none flagged"}`;
}

export function sessionContextToPrompt(
  previousSets: CvSetSummary[],
  lastAdvice?: string,
) {
  if (!previousSets.length) {
    return "";
  }

  const sets = previousSets
    .map(
      (set, index) =>
        `Set ${index + 1}: ${set.exercise}, ${set.reps} reps, form scores [${set.formScores.join(", ")}], ${set.bodyLine}, ${set.tempo}.`,
    )
    .join("\n");

  const advice = lastAdvice
    ? `\nYour previous advice was: "${lastAdvice}"`
    : "";

  return `Session so far (earlier sets, oldest first):\n${sets}${advice}\n\nRefer back to this history where relevant (progress, fatigue, whether earlier advice was applied).`;
}
