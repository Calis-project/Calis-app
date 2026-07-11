import { LM } from "@/lib/cv/poseMath";

export type ExerciseId = "pull-ups" | "push-ups" | "squats";

export type AngleTriple = [number, number, number];

export type ExerciseConfig = {
  id: ExerciseId;
  label: string;
  keyJoint: string;
  // Key angle is averaged over the visible triples (left/right side).
  triples: AngleTriple[];
  // Absolute-angle fallback used until the observed range calibrates.
  fallback: { flexedBelowDeg: number; extendedAboveDeg: number };
  // Calibration: observed range must exceed this before relative thresholds kick in.
  minRangeDeg: number;
  // Relative thresholds as a fraction of the observed min..max range.
  // Rep "top" = angle below min + enterTopPct * range; back to "bottom" above exitBottomPct.
  enterTopPct: number;
  exitBottomPct: number;
  // Body-line check (e.g. hip sag): deviation of `point` from the from->to line.
  bodyLine?: { point: AngleTriple | number[]; from: number[]; to: number[] };
  // Deviation above this fraction of body length counts as a form fault.
  bodyLineFaultPct: number;
  // Form-drop trigger: last two rep scores must both be this many points
  // below the first-half average of the set.
  formDropDeltaPts: number;
};

const ELBOW_TRIPLES: AngleTriple[] = [
  [LM.leftShoulder, LM.leftElbow, LM.leftWrist],
  [LM.rightShoulder, LM.rightElbow, LM.rightWrist],
];

const KNEE_TRIPLES: AngleTriple[] = [
  [LM.leftHip, LM.leftKnee, LM.leftAnkle],
  [LM.rightHip, LM.rightKnee, LM.rightAnkle],
];

const HIP_BODY_LINE = {
  point: [LM.leftHip, LM.rightHip],
  from: [LM.leftShoulder, LM.rightShoulder],
  to: [LM.leftAnkle, LM.rightAnkle],
};

// All tunable CV numbers live here on purpose: manual tuning edits this file,
// and the future VLM auto-calibration mode adjusts these same parameters.
export const EXERCISES: Record<ExerciseId, ExerciseConfig> = {
  "pull-ups": {
    id: "pull-ups",
    label: "Pull-ups",
    keyJoint: "elbow",
    triples: ELBOW_TRIPLES,
    fallback: { flexedBelowDeg: 100, extendedAboveDeg: 150 },
    minRangeDeg: 40,
    enterTopPct: 0.25,
    exitBottomPct: 0.75,
    bodyLine: HIP_BODY_LINE,
    bodyLineFaultPct: 0.12,
    formDropDeltaPts: 8,
  },
  "push-ups": {
    id: "push-ups",
    label: "Push-ups",
    keyJoint: "elbow",
    triples: ELBOW_TRIPLES,
    fallback: { flexedBelowDeg: 110, extendedAboveDeg: 150 },
    minRangeDeg: 35,
    enterTopPct: 0.25,
    exitBottomPct: 0.75,
    bodyLine: HIP_BODY_LINE,
    bodyLineFaultPct: 0.1,
    formDropDeltaPts: 8,
  },
  squats: {
    id: "squats",
    label: "Squats",
    keyJoint: "knee",
    triples: KNEE_TRIPLES,
    fallback: { flexedBelowDeg: 110, extendedAboveDeg: 160 },
    minRangeDeg: 45,
    enterTopPct: 0.25,
    exitBottomPct: 0.75,
    bodyLineFaultPct: 0.15,
    formDropDeltaPts: 8,
  },
};

export const EXERCISE_IDS = Object.keys(EXERCISES) as ExerciseId[];

// Seconds without a completed rep (after at least one rep) before the set ends.
export const SET_END_SECONDS = 6;
