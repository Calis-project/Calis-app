"use client";

import type { CvSnapshot } from "@/lib/cv/repCounter";

type CvReadoutProps = {
  snapshot?: CvSnapshot;
  keyJoint: string;
  cvReady: boolean;
  cvError?: string;
};

export function CvReadout({ snapshot, keyJoint, cvReady, cvError }: CvReadoutProps) {
  if (cvError) {
    return <div className="cv-readout-note error">{cvError}</div>;
  }

  if (!cvReady) {
    return <div className="cv-readout-note">Loading pose model…</div>;
  }

  if (!snapshot) {
    return (
      <div className="cv-readout-note">
        Waiting for footage — play a video or start the camera.
      </div>
    );
  }

  const lastRep = snapshot.reps[snapshot.reps.length - 1];

  return (
    <div className="cv-readout" aria-live="off">
      <div className="stat big">
        <span>Reps</span>
        <strong>{snapshot.repCount}</strong>
      </div>
      <div className="stat">
        <span>{keyJoint} angle</span>
        <strong>{snapshot.trackingLost ? "—" : `${snapshot.keyAngleDeg}°`}</strong>
      </div>
      <div className="stat">
        <span>Phase</span>
        <strong>{snapshot.phase === "flexed" ? "top" : "bottom"}</strong>
      </div>
      <div className="stat">
        <span>Set</span>
        <strong>{snapshot.setPhase}</strong>
      </div>
      <div className="stat">
        <span>Calibration</span>
        <strong>
          {snapshot.calibrated
            ? `${snapshot.observedMinDeg}°–${snapshot.observedMaxDeg}°`
            : "warming up"}
        </strong>
      </div>
      <div className="stat">
        <span>Rep at</span>
        <strong>
          ↓{snapshot.topThresholdDeg}° ↑{snapshot.bottomThresholdDeg}°
        </strong>
      </div>
      <div className="stat">
        <span>Body line</span>
        <strong>{(snapshot.bodyLineDeviationPct * 100).toFixed(1)}%</strong>
      </div>
      <div className="stat">
        <span>Last rep score</span>
        <strong>{lastRep ? lastRep.formScore : "—"}</strong>
      </div>
      {snapshot.reps.length ? (
        <div className="stat wide">
          <span>Form scores</span>
          <strong>{snapshot.reps.map((rep) => rep.formScore).join(", ")}</strong>
        </div>
      ) : null}
      {snapshot.trackingLost ? (
        <div className="cv-readout-note error wide">
          Tracking lost — make sure the full body is visible.
        </div>
      ) : null}
    </div>
  );
}
