"use client";

import {
  Activity,
  Brain,
  Eye,
  Flag,
  Layers3,
  MessageCircleQuestion,
  Play,
  RefreshCw,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { ComparisonTable, type HistoryRow } from "@/components/ComparisonTable";
import { CvReadout } from "@/components/CvReadout";
import { ResultPanel } from "@/components/ResultPanel";
import { VideoPanel, type VideoSource } from "@/components/VideoPanel";
import {
  defaultBatchedPrompt,
  defaultHybridPrompt,
  defaultVlmPrompt,
  sessionContextToPrompt,
  videoTimingInstruction,
} from "@/lib/ai/prompts";
import { BATCH_MAX_FRAMES, FRAMES_PER_CALL } from "@/lib/config/capture";
import { EXERCISES, EXERCISE_IDS, type ExerciseId } from "@/lib/cv/exercises";
import { buildSetSummary, type CvEvent } from "@/lib/cv/repCounter";
import { usePoseTracking } from "@/lib/hooks/usePoseTracking";
import { captureFrame } from "@/lib/video/captureFrame";
import type {
  AnalyzeResponse,
  CvSetSummary,
  FrameInput,
  HealthResponse,
} from "@/lib/types/analysis";

type ModeTab = "cv" | "vlm" | "hybrid";

const MAX_KEYFRAMES = 8;
const ADVICE_MEMORY_CHARS = 300;

// CV-gated hybrid: a set only earns a Gemini call when its worst rep drops below
// this form score or the CV flags a weak point. Turns CV into a cost filter.
const FORM_GATE_THRESHOLD = 70;

function setNeedsCoaching(summary: CvSetSummary) {
  const worst = summary.formScores.length ? Math.min(...summary.formScores) : 0;
  return summary.weakPoints.length > 0 || worst < FORM_GATE_THRESHOLD;
}

const tabs: { id: ModeTab; label: string; detail: string; Icon: typeof Eye }[] = [
  { id: "cv", label: "CV", detail: "on-device pose · instant · free", Icon: Activity },
  { id: "vlm", label: "VLM", detail: "Gemini snapshots · 2-4 s · per call", Icon: Eye },
  {
    id: "hybrid",
    label: "Hybrid",
    detail: "CV live + Gemini on triggers",
    Icon: Layers3,
  },
];

async function postJson(endpoint: string, body: unknown) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = (await response.json()) as AnalyzeResponse;

  if (!response.ok || !data.ok) {
    throw new Error(data.ok ? "Request failed." : data.error.message);
  }

  return data;
}

async function postFile(endpoint: string, file: File, prompt: string) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("prompt", prompt);

  const response = await fetch(endpoint, { method: "POST", body: formData });
  const data = (await response.json()) as AnalyzeResponse;

  if (!response.ok || !data.ok) {
    throw new Error(data.ok ? "Request failed." : data.error.message);
  }

  return data;
}

export function Workspace() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [tab, setTab] = useState<ModeTab>("cv");
  const [exercise, setExercise] = useState<ExerciseId>("pull-ups");
  const [source, setSource] = useState<VideoSource>("upload");
  const [videoFile, setVideoFile] = useState<File>();
  const [resetTick, setResetTick] = useState(0);

  const [prompt, setPrompt] = useState(defaultVlmPrompt);
  const [autoVlm, setAutoVlm] = useState(false);
  const [autoIntervalSec, setAutoIntervalSec] = useState(15);
  const [autoSetEnd, setAutoSetEnd] = useState(true);
  const [autoFormDrop, setAutoFormDrop] = useState(true);
  const [gateOnFormDrop, setGateOnFormDrop] = useState(false);
  const [cvEvents, setCvEvents] = useState<string[]>([]);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [result, setResult] = useState<AnalyzeResponse>();
  const [history, setHistory] = useState<HistoryRow[]>([]);
  const [sessionSets, setSessionSets] = useState<CvSetSummary[]>([]);
  const [health, setHealth] = useState<HealthResponse>();

  const busyRef = useRef(false);
  const keyframesRef = useRef<{ repIndex: number; frame: FrameInput }[]>([]);
  // One representative keyframe per completed set, kept for the batched
  // end-of-workout call (keyframesRef is cleared at each set end).
  const sessionKeyframesRef = useRef<FrameInput[]>([]);
  const lastAdviceRef = useRef<string>(undefined);
  const pendingHybridRef = useRef<{
    trigger: string;
    summary: CvSetSummary;
    frames: FrameInput[];
  }>(null);
  const flushPendingRef = useRef<() => void>(null);

  const config = EXERCISES[exercise];
  const cvActive = tab === "cv" || tab === "hybrid";
  const isLive = source === "live";

  useEffect(() => {
    let active = true;
    fetch("/api/health")
      .then((response) => response.json())
      .then((data: HealthResponse) => {
        if (active) {
          setHealth(data);
        }
      })
      .catch(() => {
        if (active) {
          setHealth(undefined);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const resetKey = useMemo(
    () => `${source}-${videoFile?.name ?? "none"}-${resetTick}`,
    [source, videoFile, resetTick],
  );

  function pushRun(data: AnalyzeResponse, label: string) {
    setResult(data);
    if (data.ok) {
      setHistory((current) => [{ ...data, label }, ...current].slice(0, 12));
      lastAdviceRef.current = data.text.slice(0, ADVICE_MEMORY_CHARS);
    }
  }

  function logCvEvent(text: string) {
    const time = new Date().toLocaleTimeString([], { hour12: false });
    setCvEvents((current) => [`${time} · ${text}`, ...current].slice(0, 12));
  }

  async function guardedCall(label: string, call: () => Promise<AnalyzeResponse>) {
    if (busyRef.current) {
      return;
    }
    busyRef.current = true;
    setBusy(true);
    setError(undefined);

    try {
      pushRun(await call(), label);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      busyRef.current = false;
      setBusy(false);
      // Fire any trigger that arrived while this call was running.
      setTimeout(() => flushPendingRef.current?.(), 0);
    }
  }

  function hybridPromptWithContext() {
    const context = sessionContextToPrompt(sessionSets, lastAdviceRef.current);
    return context ? `${prompt}\n\n${context}` : prompt;
  }

  function collectKeyframes() {
    return keyframesRef.current.slice(-FRAMES_PER_CALL).map((entry) => entry.frame);
  }

  function startHybridCall(trigger: string, summary: CvSetSummary, frames: FrameInput[]) {
    guardedCall(`hybrid (${trigger})`, () =>
      postJson("/api/analyze/hybrid", {
        prompt: hybridPromptWithContext(),
        frames,
        cvData: summary,
      }),
    );
  }

  function runHybrid(trigger: string, summary: CvSetSummary) {
    const frames = collectKeyframes();
    if (!frames.length) {
      setError("No keyframes captured yet — complete at least one rep on camera.");
      return;
    }

    if (busyRef.current) {
      pendingHybridRef.current = { trigger, summary, frames };
      logCvEvent(`${trigger}: queued — another call is running`);
      return;
    }

    startHybridCall(trigger, summary, frames);
  }

  function flushPendingHybrid() {
    const pending = pendingHybridRef.current;
    if (!pending || busyRef.current) {
      return;
    }
    pendingHybridRef.current = null;
    logCvEvent(`${pending.trigger}: running queued call`);
    startHybridCall(pending.trigger, pending.summary, pending.frames);
  }

  useEffect(() => {
    flushPendingRef.current = flushPendingHybrid;
  });

  function onCvEvent(event: CvEvent) {
    if (event.type === "rep-peak") {
      const video = videoRef.current;
      const frame = video ? captureFrame(video) : undefined;
      if (frame) {
        keyframesRef.current = [
          ...keyframesRef.current,
          { repIndex: event.repIndex, frame },
        ].slice(-MAX_KEYFRAMES);
      }
      return;
    }

    if (event.type === "rep") {
      logCvEvent(`rep ${event.rep.index} completed · score ${event.rep.formScore}`);
      return;
    }

    if (event.type === "set-end") {
      logCvEvent(`set end detected · ${event.summary.reps} reps`);
      setSessionSets((current) => [...current, event.summary]);
      // Keep one representative frame from this set for the batched call.
      const setFrame = keyframesRef.current[keyframesRef.current.length - 1]?.frame;
      if (setFrame) {
        sessionKeyframesRef.current = [
          ...sessionKeyframesRef.current,
          setFrame,
        ].slice(-BATCH_MAX_FRAMES);
      }
      if (tab === "hybrid") {
        if (!autoSetEnd) {
          logCvEvent("set end: auto call is off — skipped");
        } else if (gateOnFormDrop && !setNeedsCoaching(event.summary)) {
          logCvEvent("set end: clean set — skipped by CV gate");
        } else {
          runHybrid("set end", event.summary);
        }
      }
      keyframesRef.current = [];
      return;
    }

    if (event.type === "form-drop") {
      logCvEvent(
        `form drop detected · reps ${event.recentReps
          .map((rep) => rep.index)
          .join(", ")}`,
      );
      if (tab !== "hybrid") {
        return;
      }
      if (!autoFormDrop) {
        logCvEvent("form drop: auto call is off — skipped");
        return;
      }
      const snapshotSummary = trackingSnapshot
        ? buildSetSummary(
            trackingSnapshot.reps,
            trackingSnapshot.observedMinDeg,
            trackingSnapshot.observedMaxDeg,
            config,
          )
        : undefined;
      if (snapshotSummary) {
        runHybrid("form drop", snapshotSummary);
      }
    }
  }

  const {
    snapshot: trackingSnapshot,
    cvReady,
    cvError,
  } = usePoseTracking({
    videoRef,
    canvasRef,
    enabled: cvActive,
    exercise,
    isLive,
    onEvent: onCvEvent,
    resetKey,
  });

  function askCoach() {
    if (!trackingSnapshot || !trackingSnapshot.reps.length) {
      setError("Do some reps first so there is CV data to talk about.");
      return;
    }
    runHybrid(
      "ask coach",
      buildSetSummary(
        trackingSnapshot.reps,
        trackingSnapshot.observedMinDeg,
        trackingSnapshot.observedMaxDeg,
        config,
      ),
    );
  }

  function finishWorkout() {
    if (!sessionSets.length) {
      setError("No completed sets yet — finish at least one set first.");
      return;
    }
    const frames = sessionKeyframesRef.current.slice(-BATCH_MAX_FRAMES);
    if (!frames.length) {
      setError("No keyframes captured this session yet.");
      return;
    }
    const context = sessionContextToPrompt(sessionSets, lastAdviceRef.current);
    const batchedPrompt = context
      ? `${defaultBatchedPrompt}\n\n${context}`
      : defaultBatchedPrompt;
    const lastSummary = sessionSets[sessionSets.length - 1];
    guardedCall("hybrid (workout summary)", () =>
      postJson("/api/analyze/hybrid", {
        prompt: batchedPrompt,
        frames,
        cvData: lastSummary,
      }),
    );
  }

  function runVlmSnapshot(label: string) {
    const video = videoRef.current;
    const frame = video ? captureFrame(video) : undefined;
    if (!frame) {
      setError("No frame available — start the camera or load a video first.");
      return;
    }

    guardedCall(`vlm (${label})`, () =>
      postJson("/api/analyze/frames", { prompt, frames: [frame] }),
    );
  }

  function runVlmUpload() {
    if (!videoFile) {
      setError("Upload a video first.");
      return;
    }

    guardedCall("vlm (video)", () =>
      postFile(
        "/api/analyze/video",
        videoFile,
        `${prompt}\n\n${videoTimingInstruction}`,
      ),
    );
  }

  const runVlmSnapshotRef = useRef(runVlmSnapshot);

  useEffect(() => {
    runVlmSnapshotRef.current = runVlmSnapshot;
  });

  useEffect(() => {
    if (tab !== "vlm" || source !== "live" || !autoVlm) {
      return;
    }
    const id = setInterval(
      () => runVlmSnapshotRef.current("auto"),
      Math.max(5, autoIntervalSec) * 1000,
    );
    return () => clearInterval(id);
  }, [tab, source, autoVlm, autoIntervalSec]);

  function selectTab(next: ModeTab) {
    setTab(next);
    setError(undefined);
    setResult(undefined);
    setAutoVlm(false);
    if (next === "vlm") {
      setPrompt(defaultVlmPrompt);
    } else if (next === "hybrid") {
      setPrompt(defaultHybridPrompt);
    }
  }

  function resetSet() {
    setResetTick((tick) => tick + 1);
    keyframesRef.current = [];
    sessionKeyframesRef.current = [];
    setSessionSets([]);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">C</div>
          <div>
            <h1>Calis AI Lab</h1>
            <p>Realtime CV, VLM, and hybrid coaching lab</p>
          </div>
        </div>
        <div className="health">
          <Brain aria-hidden="true" size={17} />
          <span>{health?.model || "Gemini model"}</span>
          <strong data-ready={health?.hasKey ?? false}>
            {health?.hasKey ? "Key loaded" : "Key missing"}
          </strong>
        </div>
      </header>

      <nav className="mode-tabs" aria-label="Coaching modes">
        {tabs.map(({ id, label, detail, Icon }) => (
          <button
            data-active={tab === id}
            key={id}
            type="button"
            onClick={() => selectTab(id)}
          >
            <Icon aria-hidden="true" size={17} strokeWidth={2.1} />
            <span>
              <strong>{label}</strong>
              <small>{detail}</small>
            </span>
          </button>
        ))}
      </nav>

      <div className="workspace">
        <section className="control-panel">
          {cvActive ? (
            <div className="exercise-row">
              <label>
                <span>Exercise</span>
                <select
                  value={exercise}
                  onChange={(event) =>
                    setExercise(event.target.value as ExerciseId)
                  }
                >
                  {EXERCISE_IDS.map((id) => (
                    <option key={id} value={id}>
                      {EXERCISES[id].label}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="icon-action"
                title="Reset set and calibration"
                type="button"
                onClick={resetSet}
              >
                <RefreshCw aria-hidden="true" size={16} />
              </button>
            </div>
          ) : null}

          <VideoPanel
            canvasRef={canvasRef}
            overlayEnabled={cvActive}
            source={source}
            videoFile={videoFile}
            videoRef={videoRef}
            onSourceChange={setSource}
            onVideoFile={setVideoFile}
          />
        </section>

        <div className="output-stack">
          {cvActive ? (
            <section className="readout-panel">
              <div className="section-heading">
                <span>Live CV readout</span>
                <small>on-device</small>
              </div>
              <CvReadout
                cvError={cvError}
                cvReady={cvReady}
                keyJoint={config.keyJoint}
                snapshot={trackingSnapshot}
              />
            </section>
          ) : null}
          {tab === "cv" ? (
            <section className="cv-note">
              <div className="section-heading">
                <span>Raw CV output</span>
                <small>live · on-device · no cloud calls</small>
              </div>
              <pre className="json-view">
                {trackingSnapshot
                  ? JSON.stringify(trackingSnapshot, null, 2)
                  : "// no data yet — play a video or start the camera"}
              </pre>
            </section>
          ) : (
            <section className="call-panel">
              <div className="section-heading">
                <span>{tab === "vlm" ? "VLM controls" : "Hybrid controls"}</span>
                <small>{tab === "vlm" ? "Gemini per call" : "CV triggers Gemini"}</small>
              </div>

              <label className="prompt-box">
                <span>Prompt</span>
                <textarea
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                />
              </label>

              {tab === "vlm" ? (
                <>
                  <div className="action-row">
                    <button
                      className="primary-action"
                      disabled={busy}
                      type="button"
                      onClick={() =>
                        isLive || videoFile === undefined
                          ? runVlmSnapshot("snapshot")
                          : runVlmUpload()
                      }
                    >
                      <Play aria-hidden="true" size={17} fill="currentColor" />
                      {isLive
                        ? "Analyze now"
                        : videoFile
                          ? "Analyze full video"
                          : "Analyze now"}
                    </button>
                  </div>
                  {isLive ? (
                    <div className="auto-row">
                      <label className="auto-toggle">
                        <input
                          checked={autoVlm}
                          type="checkbox"
                          onChange={(event) => setAutoVlm(event.target.checked)}
                        />
                        <span>Auto-snapshot every</span>
                      </label>
                      <input
                        className="auto-interval"
                        disabled={!autoVlm}
                        max={120}
                        min={5}
                        type="number"
                        value={autoIntervalSec}
                        onChange={(event) =>
                          setAutoIntervalSec(Number(event.target.value) || 15)
                        }
                      />
                      <span>seconds (watch your free-tier quota)</span>
                    </div>
                  ) : null}
                </>
              ) : (
                <>
                  <div className="trigger-row">
                    <button
                      className="trigger-pill"
                      data-active={autoSetEnd}
                      title="Toggle the automatic call when a set ends"
                      type="button"
                      onClick={() => setAutoSetEnd((value) => !value)}
                    >
                      auto · set end · {autoSetEnd ? "on" : "off"}
                    </button>
                    <button
                      className="trigger-pill"
                      data-active={autoFormDrop}
                      title="Toggle the automatic call on form drop (max once per set)"
                      type="button"
                      onClick={() => setAutoFormDrop((value) => !value)}
                    >
                      auto · form drop · {autoFormDrop ? "on" : "off"}
                    </button>
                    <button
                      className="trigger-pill"
                      data-active={gateOnFormDrop}
                      title="CV gate: only call the coach on set end when form actually drops (saves free-tier calls)"
                      type="button"
                      onClick={() => setGateOnFormDrop((value) => !value)}
                    >
                      gate · only if form drops · {gateOnFormDrop ? "on" : "off"}
                    </button>
                  </div>
                  <div className="event-log" aria-label="CV events">
                    {cvEvents.length ? (
                      cvEvents.map((entry, index) => <div key={index}>{entry}</div>)
                    ) : (
                      <div>CV events appear here: reps, form drops, set end.</div>
                    )}
                  </div>
                  <div className="action-row">
                    <button
                      className="primary-action"
                      disabled={busy}
                      type="button"
                      onClick={askCoach}
                    >
                      <MessageCircleQuestion
                        aria-hidden="true"
                        size={17}
                      />
                      Ask Coach now
                    </button>
                    <button
                      className="secondary-action"
                      disabled={busy || !sessionSets.length}
                      title="Batched mode: one Gemini call reviewing the whole session"
                      type="button"
                      onClick={finishWorkout}
                    >
                      <Flag aria-hidden="true" size={16} />
                      Finish workout
                    </button>
                  </div>
                  {sessionSets.length ? (
                    <div className="session-strip">
                      {sessionSets.map((set, index) => (
                        <span className="trigger-pill" key={index}>
                          set {index + 1} · {set.reps} reps
                        </span>
                      ))}
                    </div>
                  ) : null}
                </>
              )}
            </section>
          )}

          {tab !== "cv" ? (
            <>
              <ResultPanel busy={busy} error={error} result={result} />
              <ComparisonTable rows={history} />
            </>
          ) : null}
        </div>
      </div>
    </main>
  );
}
