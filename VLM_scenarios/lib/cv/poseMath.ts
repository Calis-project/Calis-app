export type LandmarkPoint = {
  x: number;
  y: number;
  z: number;
  visibility?: number;
};

// MediaPipe Pose landmark indices (33-point model).
export const LM = {
  leftShoulder: 11,
  rightShoulder: 12,
  leftElbow: 13,
  rightElbow: 14,
  leftWrist: 15,
  rightWrist: 16,
  leftHip: 23,
  rightHip: 24,
  leftKnee: 25,
  rightKnee: 26,
  leftAnkle: 27,
  rightAnkle: 28,
} as const;

// Skeleton segments drawn on the overlay (torso + arms + legs).
export const POSE_CONNECTIONS: [number, number][] = [
  [11, 12],
  [11, 13],
  [13, 15],
  [12, 14],
  [14, 16],
  [11, 23],
  [12, 24],
  [23, 24],
  [23, 25],
  [25, 27],
  [24, 26],
  [26, 28],
  [27, 29],
  [28, 30],
  [27, 31],
  [28, 32],
];

export const MIN_VISIBILITY = 0.5;

export function isVisible(point: LandmarkPoint | undefined): point is LandmarkPoint {
  return Boolean(point) && (point?.visibility ?? 1) >= MIN_VISIBILITY;
}

// Angle at joint b (degrees, 0-180) formed by segments b->a and b->c.
export function angleDeg(a: LandmarkPoint, b: LandmarkPoint, c: LandmarkPoint) {
  const abX = a.x - b.x;
  const abY = a.y - b.y;
  const cbX = c.x - b.x;
  const cbY = c.y - b.y;
  const dot = abX * cbX + abY * cbY;
  const cross = abX * cbY - abY * cbX;
  return Math.abs((Math.atan2(cross, dot) * 180) / Math.PI);
}

export function midpoint(a: LandmarkPoint, b: LandmarkPoint): LandmarkPoint {
  return {
    x: (a.x + b.x) / 2,
    y: (a.y + b.y) / 2,
    z: (a.z + b.z) / 2,
    visibility: Math.min(a.visibility ?? 1, b.visibility ?? 1),
  };
}

// Perpendicular distance of `point` from the line through `from`/`to`,
// normalized by the line length so the result is camera-scale independent.
export function lineDeviationPct(
  point: LandmarkPoint,
  from: LandmarkPoint,
  to: LandmarkPoint,
) {
  const lineX = to.x - from.x;
  const lineY = to.y - from.y;
  const length = Math.hypot(lineX, lineY);

  if (length < 1e-6) {
    return 0;
  }

  const cross = (point.x - from.x) * lineY - (point.y - from.y) * lineX;
  return Math.abs(cross) / (length * length);
}
