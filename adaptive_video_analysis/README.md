# Calis Adaptive Video Analysis

This folder contains an isolated prototype for context-efficient calisthenics
video analysis. It scans a short clip locally, builds a timestamped pose and
motion timeline, sends only selected frames to a vision-language model, and
returns evidence-constrained JSON feedback.

The first implementation supports:

- push-up and squat repetition phases and local candidate rules
- plank, lunge, and hollow-hold generic pose timelines
- Gemini coarse-to-fine image analysis
- Groq image analysis with its smaller five-image request budget
- local-only analysis without any VLM call
- a CLI, FastAPI endpoint, privacy-safe temporary upload handling, and a
  labelled-dataset evaluation command

This is an engineering prototype, not a validated coach. Form thresholds and
model findings must be calibrated against human-reviewed clips before product
use.

## How it works

```text
30-second-or-shorter video
  -> validate and decode locally
  -> MediaPipe pose at configurable 8 FPS
  -> angles, visibility, motion, phases, repetitions
  -> coverage + phase + anomaly frame selection
  -> sparse VLM overview
  -> merge local and VLM candidate intervals
  -> denser inspection of only those intervals
  -> schema and safety validation
  -> two prioritized findings at most
```

Local pose samples do not enter the language-model context. The result reports
both `processed_local_frames` and `images_sent` so that efficiency can be
measured rather than assumed.

## Setup

PowerShell:

```powershell
cd adaptive_video_analysis
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
.\.venv\Scripts\calis-video.exe download-model --variant lite
```

For higher local pose accuracy, benchmark `full` and `heavy` instead of assuming
that their extra latency is worthwhile:

```powershell
.\.venv\Scripts\calis-video.exe download-model --variant heavy --target models\pose_landmarker_heavy.task
$env:CALIS_POSE_MODEL = "models\pose_landmarker_heavy.task"
```

Add `GEMINI_API_KEY` or `GROQ_API_KEY` to `.env`. Never expose these keys in a
browser bundle or commit the `.env` file.

## CLI

Run a no-VLM local pass:

```powershell
.\.venv\Scripts\calis-video.exe analyze video.mp4 `
  --exercise push_up `
  --provider local `
  --mode local `
  --output result.json
```

Run the default two-pass provider flow:

```powershell
.\.venv\Scripts\calis-video.exe analyze video.mp4 `
  --exercise squat `
  --provider auto `
  --mode coarse-to-fine `
  --output result.json
```

`auto` selects Gemini, then Groq, then local-only depending on configured keys.
Use `--keep-artifacts artifacts\run-name` only when explicit retention of the
selected debug frames is acceptable. Source video is never copied to that
folder.

## HTTP API

```powershell
.\.venv\Scripts\calis-video.exe serve
```

The API provides:

- `GET /health`
- `POST /v1/analyze` as multipart form data with `video`, `exercise`,
  `provider`, and `mode`
- interactive documentation at `http://127.0.0.1:8000/docs`

Uploads are written to a request-scoped temporary directory and deleted on
success or failure. The API does not expose a raw-video persistence option.

## Evaluation

Create a JSONL manifest:

```powershell
.\.venv\Scripts\calis-video.exe example-manifest
```

Then run an offline benchmark:

```powershell
.\.venv\Scripts\calis-video.exe evaluate dataset.jsonl `
  --provider local `
  --mode local `
  --output reports\local.json
```

Repeat with Gemini and Groq. The report measures repetition error, usability
classification, finding precision/recall, latency, images sent, and context
reduction. See [docs/evaluation.md](docs/evaluation.md).

## Privacy caveat: MediaPipe metrics

Current MediaPipe Tasks processes images and video on-device and states that it
does not send that input data to Google. Current packages do send performance
and utilization metrics, however, and Google says applications are responsible
for informed consent. Production deployment should therefore do one of:

1. disclose this metrics processing and collect the required consent;
2. run the CV worker in an outbound-network-blocked sandbox; or
3. replace the packaged runtime with a reviewed, telemetry-free pose backend.

The recommended production architecture is option 2: isolate local CV from the
networked provider adapter. The prototype records this as an unresolved
production gate rather than silently claiming completely offline processing.

## Current model defaults

The defaults were verified against official provider documentation on
2026-07-28:

- `gemini-3.6-flash`: GA, text/image/video input, structured output, and a free
  tier. It is the primary provider.
- `gemini-3.5-flash-lite`: free-tier fallback.
- `qwen/qwen3.6-27b` on Groq: free-plan vision fallback, limited to five images
  per request.

Provider availability and quotas change. All IDs are environment-configurable,
and they should be rechecked before deployment.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip check
```

The current automated suite covers geometry, push-up/squat phase detection,
adaptive selection, safety filtering, video decoding, two-pass orchestration,
and evaluation metrics. Live provider validation still requires API keys and
real labelled clips.

