# Calis Mobile — Flutter Camera

Issue **#8 / TSK-06** implements the live camera preview, actual `CameraImage`
stream, and stream FPS diagnostics. Functional implementation is complete;
**stable >=30 FPS performance remains pending physical Android validation**.

## Run & Validate

Use Flutter **3.47.5** / Dart **3.13.4** and an Android SDK. From `mobile/`:

```bash
flutter pub get
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
flutter devices
flutter run --profile -d <physical-android-device-id>
```

Grant camera permission. This small foreground module selects the back camera,
passes its description through `CalisApp` to `CameraScreen`, and displays **FPS**.
The image callback counts frames using a stopwatch and logs intervals over 100 ms
as diagnostics, not proof of dropped frames. No frames are saved or uploaded.

Issue **#26 / TSK-203** sends accepted camera frames to the on-device MediaPipe
Pose Landmarker through a small native platform channel. Android requests YUV420
frames; iOS requests BGRA frames. Native inference uses MediaPipe's video mode
on a background worker with increasing frame timestamps. The bridge returns normalized
`shoulder`, `elbow`, `wrist`, `hip`, `knee`, and `ankle` coordinates from the more visible
side, matching the names used by `src/vision/pose_extractor.py`. It bundles the
same lite model; the Python video-file extractor itself does not run inside the phone app.

The preview displays camera FPS, FPS with all six landmarks, and frames skipped
while detection was busy. A once-per-second log also shows processed frames and
average/maximum processing time. For issue #26 acceptance, check on a physical
phone with a person in view that landmark FPS stays at or above 15, processing
stays below 35 ms per frame, and the preview remains smooth. These numbers are
runtime diagnostics, not a benchmark claim from desktop tests. iOS also needs
`pod install` and device validation on a Mac.

There is no automatic background/resume recovery or Retry UI. Restart the app for
a fresh foreground session or after changing permissions. Use an emulator for
functional checks and a physical Android device for performance acceptance.

## Skeleton overlay

Issue #29's mock acceptance path uses the standard CameraPreview and skips
MediaPipe initialization. It has no mock toggle in the app:

```bash
flutter run --profile --dart-define=SKELETON_MOCK=true -d <device-id>
flutter build apk --profile --dart-define=SKELETON_MOCK=true
```

Without this flag, the app keeps the live pose pipeline. For 60 FPS acceptance,
measure the Flutter UI and raster timeline on a physical 60 Hz device, after
warm-up, for at least 30 seconds. The displayed Camera FPS is not UI FPS.
Record the device, display refresh rate, build flag, and timeline results.
The flag makes a test fixture available; it does not prove 60 FPS by itself.

The overlay starts in live mode and receives the latest normalized joints from
the frame-by-frame bridge using the same CameraController/CameraPreview as
mock acceptance. The direct native-camera stream is not selected by this screen.
An empty detection clears the live skeleton. The user reported successful tablet
checks (including orientation) and one teammate reported a successful test.
Precise alignment across devices/orientations and measured 60 FPS UI acceptance
remain pending; see the report for the distinction between functional checks
and performance evidence.

## Documentation

- [Camera engineering report and physical-device test protocol](../docs/04_mobile/flutter_camera_report.md)
- [Simple explanation for learning and presenting the camera task](../docs/04_mobile/flutter_camera_explained.md)
- [Issue #29 skeleton overlay report, test results and remaining acceptance checks](../docs/04_mobile/flutter_skeleton_overlay_report.md)

Generated platform scaffolding is retained. Android is the current test target;
other platform behavior is not validated by this task.
