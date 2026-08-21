import { SET_END_SECONDS, type ExerciseConfig } from "@/lib/cv/exercises";
import {
  angleDeg,
  isVisible,
  lineDeviationPct,
  midpoint,
  type LandmarkPoint,
} from "@/lib/cv/poseMath";
import type { CvSetSummary } from "@/lib/types/analysis";

const SMOOTHING_WINDOW = 5;

export type RepRecord = {
  index: number;
  minAngleDeg: number;
  maxAngleDeg: number;
  romPct: number;
  bodyLinePeakPct: number;
  durationMs: number;
  formScore: number;
};

export type SetPhase = "idle" | "active" | "ended";

export type CvSnapshot = {
  keyAngleDeg: number;
  phase: "extended" | "flexed";
  repCount: number;
  calibrated: boolean;
  observedMinDeg: number;
  observedMaxDeg: number;
  topThresholdDeg: number;
  bottomThresholdDeg: number;
  bodyLineDeviationPct: number;
  reps: RepRecord[];
  setPhase: SetPhase;
  trackingLost: boolean;
};

export type CvEvent =
  | { type: "rep"; rep: RepRecord }
  | { type: "rep-peak"; repIndex: number }
  | { type: "form-drop"; recentReps: RepRecord[] }
  | { type: "set-end"; summary: CvSetSummary };

function mean(values: number[]) {
  return values.length
    ? values.reduce((sum, value) => sum + value, 0) / values.length
    : 0;
}

function median(values: number[]) {
  if (!values.length) {
    return 0;
  }
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

// Pure so the UI can also summarize a set mid-way from a snapshot (Ask Coach).
export function buildSetSummary(
  reps: RepRecord[],
  observedMinDeg: number,
  observedMaxDeg: number,
  config: ExerciseConfig,
): CvSetSummary {
  const scores = reps.map((rep) => rep.formScore);
  const faultReps = reps
    .filter((rep) => rep.bodyLinePeakPct > config.bodyLineFaultPct)
    .map((rep) => rep.index);

  const bodyLine = !config.bodyLine
    ? "not tracked"
    : faultReps.length
      ? `hip drop detected in reps ${faultReps.join(", ")}`
      : "stable";

  const durations = reps.map((rep) => rep.durationMs);
  const half = Math.ceil(durations.length / 2);
  const earlyTempo = median(durations.slice(0, half));
  const lateTempo = median(durations.slice(half));
  const tempo =
    durations.length < 3 || !earlyTempo
      ? "too few reps to judge tempo"
      : lateTempo < earlyTempo * 0.7
        ? "controlled early, rushed final reps"
        : lateTempo > earlyTempo * 1.4
          ? "slowing down in final reps"
          : "steady tempo";

  const weakPoints: string[] = [];
  if (faultReps.length) {
    weakPoints.push("hip control");
  }
  const lateReps = reps.slice(-2);
  if (reps.length >= 4 && lateReps.every((rep) => rep.romPct < 0.75)) {
    weakPoints.push("range shrinking under fatigue");
  }
  if (scores.length >= 3 && scores[scores.length - 1] < mean(scores) - 15) {
    weakPoints.push("fatigue management");
  }

  const range = observedMaxDeg - observedMinDeg;

  return {
    exercise: config.label,
    reps: reps.length,
    formScores: scores,
    avgKeyAngleDeg: Math.round(mean(reps.map((rep) => rep.minAngleDeg))),
    keyJoint: config.keyJoint,
    rangeOfMotionDeg: Math.round(Math.max(0, Number.isFinite(range) ? range : 0)),
    bodyLine,
    tempo,
    weakPoints,
  };
}

function groupPoint(landmarks: LandmarkPoint[], indices: number[]) {
  const points = indices.map((index) => landmarks[index]).filter(isVisible);
  if (!points.length) {
    return undefined;
  }
  return points.length === 1 ? points[0] : midpoint(points[0], points[1]);
}

export class RepCounter {
  private config: ExerciseConfig;
  private angleBuffer: number[] = [];
  private phase: "extended" | "flexed" = "extended";
  private setPhase: SetPhase = "idle";
  private reps: RepRecord[] = [];
  private observedMin = Number.POSITIVE_INFINITY;
  private observedMax = Number.NEGATIVE_INFINITY;
  private repStartMs = 0;
  private repMinAngle = Number.POSITIVE_INFINITY;
  private repMaxAngle = Number.NEGATIVE_INFINITY;
  private repBodyLinePeak = 0;
  private lastRepEndMs = 0;
  private formDropFired = false;
  private lastSnapshot?: CvSnapshot;

  constructor(config: ExerciseConfig) {
    this.config = config;
  }

  reset() {
    this.angleBuffer = [];
    this.phase = "extended";
    this.setPhase = "idle";
    this.reps = [];
    this.observedMin = Number.POSITIVE_INFINITY;
    this.observedMax = Number.NEGATIVE_INFINITY;
    this.repMinAngle = Number.POSITIVE_INFINITY;
    this.repMaxAngle = Number.NEGATIVE_INFINITY;
    this.repBodyLinePeak = 0;
    this.formDropFired = false;
    this.lastSnapshot = undefined;
  }

  private measure(landmarks: LandmarkPoint[]) {
    const angles = this.config.triples
      .filter((triple) => triple.every((index) => isVisible(landmarks[index])))
      .map(([a, b, c]) => angleDeg(landmarks[a], landmarks[b], landmarks[c]));

    if (!angles.length) {
      return undefined;
    }

    let bodyLine = 0;
    if (this.config.bodyLine) {
      const point = groupPoint(landmarks, this.config.bodyLine.point as number[]);
      const from = groupPoint(landmarks, this.config.bodyLine.from);
      const to = groupPoint(landmarks, this.config.bodyLine.to);
      if (point && from && to) {
        bodyLine = lineDeviationPct(point, from, to);
      }
    }

    return { rawAngle: mean(angles), bodyLine };
  }

  private thresholds() {
    const range = this.observedMax - this.observedMin;
    const calibrated = range >= this.config.minRangeDeg;

    if (!calibrated) {
      return {
        calibrated,
        top: this.config.fallback.flexedBelowDeg,
        bottom: this.config.fallback.extendedAboveDeg,
      };
    }

    return {
      calibrated,
      top: this.observedMin + this.config.enterTopPct * range,
      bottom: this.observedMin + this.config.exitBottomPct * range,
    };
  }

  private scoreRep(durationMs: number): RepRecord {
    const range = Math.max(1, this.observedMax - this.observedMin);
    const romPct = Math.min(1, (this.repMaxAngle - this.repMinAngle) / range);
    const bodyComponent =
      1 - Math.min(1, this.repBodyLinePeak / this.config.bodyLineFaultPct);

    const previousDurations = this.reps.map((rep) => rep.durationMs);
    const medianDuration = median(previousDurations);
    const tempoDelta = medianDuration
      ? Math.abs(durationMs - medianDuration) / medianDuration
      : 0;
    const tempoComponent = 1 - Math.min(1, tempoDelta);

    const weights = this.config.bodyLine
      ? { rom: 0.5, body: 0.3, tempo: 0.2 }
      : { rom: 0.7, body: 0, tempo: 0.3 };

    const formScore = Math.round(
      100 *
        (weights.rom * romPct +
          weights.body * bodyComponent +
          weights.tempo * tempoComponent),
    );

    return {
      index: this.reps.length + 1,
      minAngleDeg: Math.round(this.repMinAngle),
      maxAngleDeg: Math.round(this.repMaxAngle),
      romPct,
      bodyLinePeakPct: this.repBodyLinePeak,
      durationMs,
      formScore: Math.max(0, Math.min(100, formScore)),
    };
  }

  private detectFormDrop(): RepRecord[] | undefined {
    if (this.formDropFired || this.reps.length < 3) {
      return undefined;
    }

    const scores = this.reps.map((rep) => rep.formScore);
    const baseline = mean(scores.slice(0, Math.ceil(scores.length / 2)));
    const lastTwo = scores.slice(-2);

    if (lastTwo.every((score) => score < baseline - this.config.formDropDeltaPts)) {
      this.formDropFired = true;
      return this.reps.slice(-2);
    }

    return undefined;
  }

  buildSummary(): CvSetSummary {
    return buildSetSummary(
      this.reps,
      this.observedMin,
      this.observedMax,
      this.config,
    );
  }

  // Angle/overlay preview without advancing rep state — used while scrubbing.
  preview(landmarks: LandmarkPoint[]): CvSnapshot {
    const measured = this.measure(landmarks);
    const base = this.snapshot(measured?.rawAngle, measured?.bodyLine);
    return { ...base, trackingLost: !measured };
  }

  private snapshot(angle?: number, bodyLine?: number): CvSnapshot {
    const { calibrated, top, bottom } = this.thresholds();
    return {
      keyAngleDeg: Math.round(angle ?? this.lastSnapshot?.keyAngleDeg ?? 0),
      phase: this.phase,
      repCount: this.reps.length,
      calibrated,
      observedMinDeg: Number.isFinite(this.observedMin)
        ? Math.round(this.observedMin)
        : 0,
      observedMaxDeg: Number.isFinite(this.observedMax)
        ? Math.round(this.observedMax)
        : 0,
      topThresholdDeg: Math.round(top),
      bottomThresholdDeg: Math.round(bottom),
      bodyLineDeviationPct: bodyLine ?? 0,
      reps: [...this.reps],
      setPhase: this.setPhase,
      trackingLost: false,
    };
  }

  update(
    landmarks: LandmarkPoint[],
    timestampMs: number,
  ): { snapshot: CvSnapshot; events: CvEvent[] } {
    const events: CvEvent[] = [];
    const measured = this.measure(landmarks);

    if (!measured) {
      const snapshot = {
        ...(this.lastSnapshot ?? this.snapshot()),
        trackingLost: true,
      };
      return { snapshot, events };
    }

    this.angleBuffer.push(measured.rawAngle);
    if (this.angleBuffer.length > SMOOTHING_WINDOW) {
      this.angleBuffer.shift();
    }
    const angle = mean(this.angleBuffer);

    this.observedMin = Math.min(this.observedMin, angle);
    this.observedMax = Math.max(this.observedMax, angle);

    const { top, bottom } = this.thresholds();

    if (this.phase === "extended" && angle <= top) {
      if (this.setPhase === "ended") {
        // New set starts: keep calibration, clear rep history.
        this.reps = [];
        this.formDropFired = false;
      }
      this.phase = "flexed";
      this.setPhase = "active";
      this.repStartMs = timestampMs;
      this.repMinAngle = angle;
      this.repMaxAngle = this.lastSnapshot?.keyAngleDeg ?? angle;
      this.repBodyLinePeak = measured.bodyLine;
      events.push({ type: "rep-peak", repIndex: this.reps.length + 1 });
    } else if (this.phase === "flexed") {
      this.repMinAngle = Math.min(this.repMinAngle, angle);
      this.repMaxAngle = Math.max(this.repMaxAngle, angle);
      this.repBodyLinePeak = Math.max(this.repBodyLinePeak, measured.bodyLine);

      if (angle >= bottom) {
        const rep = this.scoreRep(timestampMs - this.repStartMs);
        this.reps.push(rep);
        this.phase = "extended";
        this.lastRepEndMs = timestampMs;
        events.push({ type: "rep", rep });

        const droppedReps = this.detectFormDrop();
        if (droppedReps) {
          events.push({ type: "form-drop", recentReps: droppedReps });
        }
      }
    }

    if (
      this.setPhase === "active" &&
      this.phase === "extended" &&
      this.reps.length > 0 &&
      timestampMs - this.lastRepEndMs > SET_END_SECONDS * 1000
    ) {
      this.setPhase = "ended";
      events.push({ type: "set-end", summary: this.buildSummary() });
    }

    const snapshot = this.snapshot(angle, measured.bodyLine);
    this.lastSnapshot = snapshot;
    return { snapshot, events };
  }
}
