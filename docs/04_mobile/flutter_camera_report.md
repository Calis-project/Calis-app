# Flutter Camera Stream & Real-time Preview — Engineering Report

- **Document ID:** TSK-06-CAMERA-REPORT
- **Task / Issue:** [#8 — TSK-06](https://github.com/Calis-project/Calis-app/issues/8)
- **Sprint:** Sprint 01
- **Owner:** Arash
- **Working Branch:** `feat/issue-8-flutter-camera`
- **Review Date:** 2026-09-24
- **Functional Implementation:** Complete
- **Emulator Functional Validation:** Complete (foreground smoke-test scope)
- **Static Analysis / Tests:** Passed (restoration validation, 2026-09-24)
- **Physical-device >=30 FPS Validation:** Pending

---

## 1. Objective & Scope

Provide a live full-screen camera preview and real `CameraImage` callbacks for
Calis, with measured image-stream FPS. The acceptance target is **stable >=30 FPS
without frame drops**. Preview smoothness alone does not establish this target.

This is a small, educational foreground camera module. It does not implement
MediaPipe, pose estimation, recording, saved images, backend integration, automatic lifecycle restart, or runtime recovery.
Generated platform scaffolding is retained; Android is the validation target.

## 2. Implementation & Data Flow

```text
main()
  -> WidgetsFlutterBinding.ensureInitialized()
  -> availableCameras() -> select back CameraDescription
  -> CalisApp(camera) -> CameraScreen(camera)
      -> initState() -> CameraController
          -> initialize()
          -> CameraPreview -> User
          -> startImageStream() -> CameraImage callbacks
              -> frame count / elapsed seconds -> FPS overlay and log
              -> future CV / MediaPipe integration (not implemented)
```

The controller is created in `initState()` with `ResolutionPreset.high` and
`enableAudio: false`. After initialization, the app starts its stopwatch and
image stream. The `Stack` contains `CameraPreview` and the `FPS:` text
overlay. A small cover-fit wrapper preserves image proportions while filling the
screen, cropping edges where camera and screen aspect ratios differ. System bars
are not forcibly hidden.

The app requires a back camera. If none exists, or enumeration throws a
`CameraException`, `main()` displays plain error text. Controller initialization
and stream-start `CameraException`s also produce plain error text. There is no
front-camera fallback or Retry UI. After correcting permission in Settings,
restart the app.

`CameraPreview` shows the native camera view. `CameraImage` provides pixel planes
and metadata to Dart. The two delivery paths are distinct: all FPS counts come
from **`CameraImage` callbacks**, never preview rendering. The application does
not copy, retain, queue, save, or upload those images.

### Important Files

| File | Responsibility |
| :--- | :--- |
| `mobile/lib/main.dart` | Entire camera feature, inline timing, preview, startup error text, and cleanup |
| `mobile/test/widget_test.dart` | Three focused startup-error tests; only camera enumeration is simulated |
| `mobile/pubspec.yaml` / `mobile/pubspec.lock` | Package requirements / resolved versions |
| `mobile/.gitignore` | Excludes generated/local files; allows the app lockfile |
| `mobile/ios/Runner/Info.plist` | Camera permission usage description |
| `mobile/README.md` | Run/test commands and report links |

## 3. FPS & Frame Interval Measurements

The callback increments `_frameCount`. Using the stopwatch's millisecond timestamp:

```text
elapsedSeconds = (currentTimestamp - fpsWindowStart) / 1000.0
FPS = frameCount / elapsedSeconds
```

Once at least one second has elapsed, that callback updates `_fps` with
`setState()`, logs the result, resets the frame count, and advances the reporting
window's start timestamp. For example, 30 callbacks in 1.2 seconds means 25 FPS.
`setState()` is not called for every frame.

The stopwatch starts **after initialization** so camera setup time is excluded.
It remains continuous between reporting windows, keeping consecutive frame
timestamps comparable even when an interval crosses a window boundary.

Each callback also subtracts the preceding frame timestamp. Intervals **strictly
>100 ms** are logged as a **long frame interval diagnostic**. This is a heuristic,
not a dropped-frame detector. A 50 ms gap also exceeds nominal 30 FPS spacing,
but does not cross this coarse threshold. Callback timing cannot establish sensor
frame loss, native buffering, or inference throughput.

Reporting remains callback-driven: if callbacks stop, the last displayed FPS
remains visible until another callback arrives. There is no reporting timer,
silent-stream zero update, maximum-interval summary, or separate metrics helper.
Dart scheduling delays and initial stream startup latency affect the measured
callback rate. Measurements do not use sensor capture timestamps.

## 4. Resource Management & Package Constraints

Resolved packages are `camera 0.12.1`, `camera_android_camerax 0.7.4+8`, and
`camera_platform_interface 2.14.0`. The platform interface is a transitive dependency.

A `mounted` check after initialization prevents starting a stream after the screen
has been removed. Callback and post-await checks avoid updating a disposed widget.
`dispose()` stops the stopwatch and starts a small asynchronous cleanup method.
That method stops an active image stream and attempts controller disposal even
if stopping fails; cleanup errors are logged. In this package version, controller
`dispose()` waits for pending initialization internally.

The exact controller source was reviewed: `camera 0.12.1`'s `dispose()` releases
native resources but does not cancel its Dart image-stream subscription.
`stopImageStream()` performs that cancellation, so the explicit stop is retained.

**Foreground-only limitation:** the [camera package documentation](https://pub.dev/packages/camera/versions/0.12.1)
requires application-managed lifecycle handling for reliable background/resume
operation. The current implementation has no `WidgetsBindingObserver`, automatic
background release, or resume reinitialization. Widget disposal is not the same
as putting the app in the background. Background/resume behavior is not guaranteed;
restart the app for a fresh foreground session. This is a deliberate limitation
of the current scope, not a claim that the package handles lifecycle itself.

There is no runtime camera-error listener or automatic recovery. Also, CameraX
starts native image analysis asynchronously; awaiting `startImageStream()` does
not catch every possible asynchronous backend failure. These limitations are
not hidden by the startup `CameraException` guards.

Android's camera permission comes from the CameraX library manifest. Flutter
3.47.5 defaults to minimum Android SDK 24, matching this package's requirement.
The retained iOS scaffold has `NSCameraUsageDescription`; iOS is unvalidated.
Audio stays disabled. Native cleanup failures are logged, not proof of release.

## 5. Engineering Decisions & Trade-offs

| Decision | Reason | Trade-off |
| :--- | :--- | :--- |
| Back camera, high resolution, audio disabled | Preserve the Issue #8 camera configuration | Back camera required; no emulator-driven resolution tuning |
| Callback-based `frameCount / elapsedSeconds` | Measure real image delivery with simple inline logic | Display retains the last value during a stalled stream |
| Continuous stopwatch and separate FPS window start | Keep frame intervals correct across reporting boundaries | One extra integer timestamp |
| Explicit stream stop before disposal | Cancel the Dart subscription as well as release native resources | Small asynchronous cleanup method; failures are logged |
| Cover-fit preview | Fill the screen while preserving proportions | Crops edges; future overlays must account for this transform |
| Plain startup errors and foreground-only operation | Keep this task's implementation small | No automatic recovery, Retry UI, or background/resume guarantee |

## 6. Validation

The following checks passed on 2026-09-24 using **Windows Flutter 3.47.5 /
Dart 3.13.4**, directly against the current implementation in `mobile/`. This
documentation-only reorganization does not change code or rerun those checks.

| Command | Result |
| :--- | :--- |
| `dart format lib test` | Pass; two hand-written Dart files formatted |
| `dart format --output=none --set-exit-if-changed lib test` | Pass; zero changes |
| `flutter analyze` | Pass; no issues found |
| `flutter test` | Pass; all three tests |

The three tests cover no cameras, a front-only device, and a camera enumeration
exception. They simulate only the enumeration method channel and exercise the
app's startup error path. They do not test native camera operation, actual frames,
FPS, disposal, or permissions on hardware.

### Emulator Evidence

The original task handoff reports successful functional debug/profile emulator
testing, commonly around **15–26 FPS**, with occasional **>100 ms** intervals and
larger delays. Those observations do not establish physical-phone performance
and are not treated as proof of an implementation performance failure.

During the 2026-09-24 restoration validation, `flutter run -d emulator-5554 --debug`
built and launched successfully on `sdk gphone16k x86 64`, Android 17 / API 37 (x86_64). A captured log segment
contained 63 FPS reports ranging from **0.2 to 30.5 FPS**, including startup, and
119 logged long intervals with a maximum of **864 ms**. No Flutter error or
exception appeared in that captured segment. The app was stopped after the check.
This confirms native launch and image callback delivery; it is not a sustained
performance pass, a complete device test, or a physical-phone result. Preview
rotation and permission flows were not exercised in this smoke test.

## 7. Run & Physical-device Handoff

From the repository root:

```bash
cd mobile
flutter pub get
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
flutter devices
flutter run --profile -d <physical-android-device-id>
```

For an emulator functional check, use `flutter run -d <android-emulator-id>`.
Grant camera permission and check that the view changes with scene movement,
that the `FPS:` overlay updates, and that callback FPS appears in the console.

A teammate with a **physical Android device** must perform final performance
validation. Record phone/Android versions, build mode, lighting, orientation,
resolved camera dimensions, and thermal conditions. After startup settles, retain
at least 60 seconds of foreground FPS/interval logs as a proposed repeatable test.
Check sustained callback rate and investigate gaps; a smooth preview or absence
of >100 ms logs does not prove zero dropped frames. Actual drop claims need
additional native evidence. Keep high resolution unless physical measurements
justify a separate tuning change. Check real-device preview framing/rotation and
permission denial as well. Background/resume recovery is outside this version.

## 8. Acceptance Status & Future Work

| Criterion | Status |
| :--- | :--- |
| Functional implementation | **Complete** |
| Camera preview, image stream, FPS display | Working; emulator functional validation complete |
| Static analysis / automated tests | **Passed**; no analyzer issues, three tests |
| Stable >=30 FPS | **Pending physical Android validation** |
| No frame drops | **Pending; diagnostic threshold cannot prove this** |

The simple foreground implementation is complete. Emulator validation establishes
functionality only. **Issue #8's performance acceptance remains pending** until
a teammate supplies physical Android evidence.

The future CV/MediaPipe integration point is the `CameraImage image` argument in
`startImageStream()` inside `main.dart`. Future work must consider pixel planes,
orientation, processing rate, and mapping landmarks onto the cropped preview.
None of that work, or lifecycle/recovery expansion, is implemented here.
