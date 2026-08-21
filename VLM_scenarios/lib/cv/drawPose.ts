import { POSE_CONNECTIONS, type LandmarkPoint } from "@/lib/cv/poseMath";

const LINE_COLOR = "rgba(126, 231, 135, 0.85)";
const DOT_COLOR = "#7ee787";
const LOW_CONFIDENCE_DOT = "rgba(255, 141, 141, 0.9)";

export function drawPose(
  ctx: CanvasRenderingContext2D,
  landmarks: LandmarkPoint[] | undefined,
  width: number,
  height: number,
) {
  ctx.clearRect(0, 0, width, height);

  if (!landmarks) {
    return;
  }

  ctx.lineWidth = Math.max(2, width / 320);
  ctx.strokeStyle = LINE_COLOR;

  for (const [from, to] of POSE_CONNECTIONS) {
    const a = landmarks[from];
    const b = landmarks[to];
    if (!a || !b) {
      continue;
    }
    ctx.beginPath();
    ctx.moveTo(a.x * width, a.y * height);
    ctx.lineTo(b.x * width, b.y * height);
    ctx.stroke();
  }

  const radius = Math.max(3, width / 220);
  for (const point of landmarks) {
    if (!point) {
      continue;
    }
    ctx.fillStyle =
      (point.visibility ?? 1) >= 0.5 ? DOT_COLOR : LOW_CONFIDENCE_DOT;
    ctx.beginPath();
    ctx.arc(point.x * width, point.y * height, radius, 0, Math.PI * 2);
    ctx.fill();
  }
}
