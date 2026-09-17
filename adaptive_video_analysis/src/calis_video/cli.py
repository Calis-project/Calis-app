from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import PACKAGE_ROOT, Settings
from .env import load_env_file
from .evaluation import evaluate_manifest, example_manifest, load_manifest
from .factory import make_provider
from .pipeline import AdaptiveVideoAnalyzer
from .pose import download_pose_model
from .providers.base import ImageInput
from .providers.prompts import overview_prompt
from .schemas import ExerciseId


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calis-video",
        description="Context-efficient calisthenics video analysis",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze one short clip")
    analyze.add_argument("video", type=Path)
    analyze.add_argument(
        "--exercise",
        required=True,
        choices=[exercise.value for exercise in ExerciseId],
    )
    analyze.add_argument(
        "--provider",
        choices=["auto", "gemini", "groq", "local"],
        default="auto",
    )
    analyze.add_argument(
        "--mode",
        choices=["coarse-to-fine", "single", "local"],
        default="coarse-to-fine",
    )
    analyze.add_argument("--output", type=Path)
    analyze.add_argument(
        "--keep-artifacts",
        type=Path,
        help="Opt in to retaining only selected debug frames",
    )

    model = subparsers.add_parser(
        "download-model", help="Download a MediaPipe pose model"
    )
    model.add_argument(
        "--variant", choices=["lite", "full", "heavy"], default="lite"
    )
    model.add_argument("--target", type=Path)

    serve = subparsers.add_parser("serve", help="Start the local HTTP API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    evaluate = subparsers.add_parser(
        "evaluate", help="Evaluate a labelled JSONL video manifest"
    )
    evaluate.add_argument("manifest", type=Path)
    evaluate.add_argument(
        "--provider",
        choices=["auto", "gemini", "groq", "local"],
        default="local",
    )
    evaluate.add_argument(
        "--mode",
        choices=["coarse-to-fine", "single", "local"],
        default="local",
    )
    evaluate.add_argument("--limit", type=int)
    evaluate.add_argument("--output", type=Path, required=True)

    manifest = subparsers.add_parser(
        "example-manifest", help="Print one JSONL label example"
    )

    smoke = subparsers.add_parser(
        "provider-smoke",
        help="Make one minimal structured-output provider request",
    )
    smoke.add_argument("--provider", choices=["gemini", "groq"], required=True)
    return parser


def main() -> None:
    load_env_file(PACKAGE_ROOT / ".env")
    arguments = _parser().parse_args()
    settings = Settings.from_env()

    if arguments.command == "download-model":
        target = arguments.target or settings.pose_model_path
        downloaded = download_pose_model(target, arguments.variant)
        print(downloaded.resolve())
        return
    if arguments.command == "serve":
        import uvicorn

        uvicorn.run(
            "calis_video.api:app",
            host=arguments.host,
            port=arguments.port,
        )
        return
    if arguments.command == "example-manifest":
        print(example_manifest())
        return
    if arguments.command == "provider-smoke":
        import cv2
        import numpy as np

        provider = make_provider(arguments.provider, settings)
        frame = np.zeros((160, 240, 3), dtype=np.uint8)
        cv2.rectangle(frame, (55, 30), (185, 130), (255, 255, 255), 3)
        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            raise RuntimeError("Could not create provider smoke-test image")
        context = {
            "exercise": "push_up",
            "metadata": {"duration_seconds": 1.0},
            "purpose": (
                "Provider compatibility smoke test. This generated image is "
                "not exercise footage."
            ),
        }
        observation = provider.observe(
            prompt=overview_prompt(context),
            images=[
                ImageInput(
                    jpeg=encoded.tobytes(),
                    timestamp_seconds=0.5,
                    reasons=("provider_smoke_test",),
                )
            ],
            context=context,
        )
        print(observation.model_dump_json(indent=2))
        return
    if arguments.command == "evaluate":
        provider = make_provider(arguments.provider, settings)
        analyzer = AdaptiveVideoAnalyzer(settings=settings, provider=provider)
        report = evaluate_manifest(
            analyzer,
            load_manifest(arguments.manifest),
            mode=arguments.mode,
            limit=arguments.limit,
        )
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(
            report.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        print(arguments.output.resolve())
        return

    try:
        provider = make_provider(arguments.provider, settings)
        analyzer = AdaptiveVideoAnalyzer(settings=settings, provider=provider)
        result = analyzer.analyze(
            arguments.video,
            ExerciseId(arguments.exercise),
            mode=arguments.mode,
            keep_artifacts=arguments.keep_artifacts,
        )
        output = result.model_dump_json(indent=2)
        if arguments.output:
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_text(output + "\n", encoding="utf-8")
            print(arguments.output.resolve())
        else:
            print(output)
    except Exception as error:
        print(
            json.dumps({"error": type(error).__name__, "detail": str(error)}),
            file=sys.stderr,
        )
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
