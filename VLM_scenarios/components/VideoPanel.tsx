"use client";

import { Camera, Pause, Play, Upload } from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
  type RefObject,
} from "react";

import { FileDrop } from "@/components/FileDrop";

export type VideoSource = "upload" | "live";

type VideoPanelProps = {
  videoRef: RefObject<HTMLVideoElement | null>;
  canvasRef: RefObject<HTMLCanvasElement | null>;
  source: VideoSource;
  onSourceChange: (source: VideoSource) => void;
  videoFile?: File;
  onVideoFile: (file: File) => void;
  overlayEnabled: boolean;
};

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds)) {
    return "0:00";
  }
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function VideoPanel({
  videoRef,
  canvasRef,
  source,
  onSourceChange,
  videoFile,
  onVideoFile,
  overlayEnabled,
}: VideoPanelProps) {
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [cameraError, setCameraError] = useState<string>();
  const objectUrlRef = useRef<string>(null);
  const replaceInputRef = useRef<HTMLInputElement>(null);

  // Attach the chosen source to the shared <video> element.
  useEffect(() => {
    const video = videoRef.current;
    if (!video) {
      return;
    }

    setCameraError(undefined);
    setPlaying(false);
    setCurrentTime(0);
    setDuration(0);

    if (source === "live") {
      let stream: MediaStream | undefined;
      let cancelled = false;

      video.removeAttribute("src");
      video.srcObject = null;

      navigator.mediaDevices
        .getUserMedia({
          video: { facingMode: "user", width: { ideal: 1280 } },
          audio: false,
        })
        .then((mediaStream) => {
          if (cancelled) {
            mediaStream.getTracks().forEach((track) => track.stop());
            return;
          }
          stream = mediaStream;
          video.srcObject = mediaStream;
          video.muted = true;
          return video.play();
        })
        .then(() => setPlaying(true))
        .catch((error: unknown) => {
          if (!cancelled) {
            setCameraError(
              error instanceof Error
                ? `Camera unavailable: ${error.message}`
                : "Camera unavailable.",
            );
          }
        });

      return () => {
        cancelled = true;
        stream?.getTracks().forEach((track) => track.stop());
        video.srcObject = null;
      };
    }

    video.srcObject = null;
    if (videoFile) {
      const url = URL.createObjectURL(videoFile);
      objectUrlRef.current = url;
      video.src = url;
      video.muted = true;
      video.load();
    } else {
      video.removeAttribute("src");
    }

    return () => {
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
  }, [source, videoFile, videoRef]);

  function togglePlay() {
    const video = videoRef.current;
    if (!video || source === "live") {
      return;
    }
    if (video.paused) {
      video.play().catch(() => undefined);
    } else {
      video.pause();
    }
  }

  function onScrub(value: number) {
    const video = videoRef.current;
    if (!video) {
      return;
    }
    video.currentTime = value;
    setCurrentTime(value);
  }

  const showUploadPrompt = source === "upload" && !videoFile;

  return (
    <div className="video-panel">
      <input
        accept="video/*"
        hidden
        ref={replaceInputRef}
        type="file"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) {
            onVideoFile(file);
          }
          event.target.value = "";
        }}
      />

      <div className="source-toggle" role="tablist" aria-label="Video source">
        <button
          data-active={source === "upload"}
          title={videoFile ? "Pick a different video" : "Upload a video"}
          type="button"
          onClick={() => {
            if (source !== "upload") {
              onSourceChange("upload");
            } else if (videoFile) {
              replaceInputRef.current?.click();
            }
          }}
        >
          <Upload aria-hidden="true" size={15} />
          Upload
        </button>
        <button
          data-active={source === "live"}
          type="button"
          onClick={() => onSourceChange("live")}
        >
          <Camera aria-hidden="true" size={15} />
          Live camera
        </button>
      </div>

      {showUploadPrompt ? (
        <FileDrop
          accept="video/*"
          label="Choose or drop a video"
          subLabel="Video ready"
          onFile={onVideoFile}
        />
      ) : null}

      <div className="video-stage" data-empty={showUploadPrompt}>
        <video
          playsInline
          ref={videoRef}
          onLoadedMetadata={(event) => setDuration(event.currentTarget.duration)}
          onPause={() => setPlaying(false)}
          onPlay={() => setPlaying(true)}
          onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
        />
        <canvas data-visible={overlayEnabled} ref={canvasRef} />
        {cameraError ? <div className="stage-note">{cameraError}</div> : null}
        {showUploadPrompt ? (
          <div className="stage-note">
            Upload a clip, or switch to the live camera. Film side-on with your
            full body in frame, 2-3 m away.
          </div>
        ) : null}
      </div>

      {source === "upload" && videoFile ? (
        <>
          <div className="video-controls">
            <button
              className="icon-action"
              title={playing ? "Pause" : "Play"}
              type="button"
              onClick={togglePlay}
            >
              {playing ? (
                <Pause aria-hidden="true" size={16} fill="currentColor" />
              ) : (
                <Play aria-hidden="true" size={16} fill="currentColor" />
              )}
            </button>
            <input
              aria-label="Scrub video"
              max={duration || 0}
              min={0}
              step={0.05}
              type="range"
              value={currentTime}
              onChange={(event) => onScrub(Number(event.target.value))}
            />
            <span className="time-label">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>
          <div className="file-meta">
            {videoFile.name} — click Upload to replace
          </div>
        </>
      ) : null}
    </div>
  );
}
