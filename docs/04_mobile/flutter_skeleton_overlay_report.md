# Live Skeleton Canvas Overlay — Engineering Report

- **Task:** [Issue #29 — TSK-201](https://github.com/Calis-project/Calis-app/issues/29)
- **Owner:** Arash
- **Working branch:** `feat/issue-29-skeleton-overlay`
- **Validation date:** 2026-10-09
- **Implementation:** Animated mock overlay implemented
- **Automated validation:** 12 tests passed; analyzer found no issues
- **Acceptance:** **Pending — the 60 FPS UI requirement has not been demonstrated**

## 1. Scope and acceptance

Issue #29 requires a transparent `CustomPainter` above `CameraPreview`, normalized
joint coordinates, joint circles and connecting bones, and matching canvas/camera
geometry. Its acceptance criterion is smooth mock rendering at **60 FPS in the UI
layer**. Camera callback FPS is a separate measurement.

| Requirement | Current evidence | Status |
|---|---|---|
| Deliver `mobile/lib/widgets/skeleton_overlay.dart` | Overlay and painter exist | Implemented |
| Accept normalized `(x, y)` points | `Map<String, Offset>` input | Implemented |
| Draw shoulder, elbow, wrist, hip, knee and ankle | Six animated mock joints, five connections | Implemented |
| Transparent overlay over live preview | Camera remains visible behind circles/lines | Emulator checked |
| Match displayed camera geometry | Shared oriented `previewSize`, centered cover mapping; three numerical mapping fixtures | Mock transform checked; physical rotation/frame geometry pending |
| Smooth mock rendering at 60 UI FPS | Profile-mode emulator measurements below | **Not demonstrated** |

This task does not implement MediaPipe, pose inference, exercise classification,
biomechanics, recording or backend integration. The moving points are synthetic;
they do not follow a person in the camera scene.

## 2. Implementation

| File | Responsibility |
|---|---|
| `mobile/lib/widgets/skeleton_overlay.dart` | Map normalized points to canvas; draw joints and bones |
| `mobile/lib/main.dart` | Camera preview, mock animation, visibility controls and camera FPS label |
| `mobile/test/skeleton_overlay_test.dart` | Nine painter/geometry tests |
| `mobile/test/widget_test.dart` | Three existing camera-startup error tests |

`CameraPreview` and the overlay are siblings in a full-screen `Stack`. The preview
uses centered `BoxFit.cover` inside `ClipRect`; the canvas receives the same
oriented preview dimensions. The painter uses:

```text
scale = max(canvasWidth / cameraWidth, canvasHeight / cameraHeight)
cropX = (cameraWidth * scale - canvasWidth) / 2
cropY = (cameraHeight * scale - canvasHeight) / 2
canvasX = normalizedX * cameraWidth * scale - cropX
canvasY = normalizedY * cameraHeight * scale - cropY
```

Cover fitting crops excess image edges. Therefore a normalized edge point can
correctly map outside the visible canvas. This does not establish alignment with
future model inputs, which may have their own rotation, resize or crop transform.
Actual `CameraImage` dimensions were not independently instrumented in these tests.

Connections are shoulder–elbow, elbow–wrist, shoulder–hip, hip–knee and knee–ankle.
Missing endpoints skip their bone; available joints still draw. An empty map draws
nothing. Green joints have radius 6 with a black radius-8 outline; green bones have
width 3 over a black width-5 outline. The painter does not fill the background.

A two-second `AnimationController` repeats in reverse, shifting all mock points
horizontally. `AnimatedBuilder` rebuilds the mock overlay on animation ticks;
the camera preview is outside that builder. The painter compares map identity and
camera dimensions in `shouldRepaint`. Callers should provide a new map when pose
data changes; mutating the same map in place is not a supported repaint contract.
The optional `super.repaint` parameter exists but is not used by the current mock.

**Hide mock** removes the overlay and stops its animation. **Show mock** resumes
it. The bottom label identifies the data as a mock. **Camera FPS** reports
`CameraImage` callback delivery, not Flutter UI or inference FPS. The camera module
is documented separately in [the camera report](flutter_camera_report.md).

## 3. Automated and manual validation

Final automated checks on 2026-10-09:

```bash
cd mobile
flutter test --no-pub
flutter analyze --no-pub
```

Results: **12 tests passed**, **No issues found**. The nine painter tests cover
outlined drawing, portrait horizontal cropping, landscape vertical cropping,
matching aspect ratios, missing joints, empty input, changed pose, changed camera
dimensions and unchanged map/dimensions. The three startup tests simulate no
cameras, a front-only device and camera enumeration failure. They do not validate
the native camera, permission dialogs, button interaction or UI frame timing.

Manual target: Android emulator-5554, sdk gphone16k x86_64, profile mode, Impeller
OpenGLES; resolved camera 0.12.1 / camera_android_camerax 0.7.4+8.

| Check | Observed result |
|---|---|
| Hide/show mock | Skeleton disappears/returns; camera stays visible |
| Home, wait, return | Same process; camera disconnects in background and delivers frames after return |
| Screen sleep/wake | Screen confirmed asleep; preview and callbacks return after wake |
| Portrait/landscape layout | Preview, joints and controls visible; no sampled black screen |
| Earlier whole-screen black output | Reproduced even with a temporary plain scaffold; emulator reboot restored output; no permanent code fix |

Home and sleep checks each covered one short cycle on this emulator. Native
CameraX behavior observed here does not replace application-managed lifecycle
handling: the app has no `WidgetsBindingObserver` or explicit resume recovery.
Secure lock screens, repeated interruption, permission revocation and other devices
remain unvalidated.

## 4. Performance and sustained operation

Before/after mock visibility measurements used four approximately 60-second VM
collections. The rolling timeline retained only the last 22–25 seconds per capture.
The figures below summarize paired `GPURasterizer::Draw` timeline spans; they are
not direct GPU execution measurements or end-to-end dropped-frame counts.

| Profile state | Mean raster draw span |
|---|---:|
| Mock visible, two captures | 26.62 / 29.17 ms |
| Mock hidden, two captures | 23.79 / 24.95 ms |
| Experimental `RepaintBoundary`, visible | 29.77 / 32.53 ms |
| Hidden in the experimental build | 30.50 ms |

These observations do not demonstrate 60 FPS. Hiding the mock reduced some UI
work, but slow raster spans remained common. A `RepaintBoundary` trial did not
establish a consistent benefit and was removed. The hidden baseline also varied
between runs, so these sequential emulator measurements cannot prove a regression
caused by the wrapper. No camera resolution reduction or speculative rotation fix
was retained.

A separate foreground soak kept camera and animated mock active for five minutes:

| Elapsed seconds | Total process PSS, MiB | Mean reported camera FPS in preceding interval |
|---:|---:|---:|
| 0.01 | 143.98 | — |
| 60.45 | 137.91 | 6.32 |
| 120.21 | 149.78 | 6.34 |
| 180.31 | 137.53 | 6.41 |
| 240.07 | 138.25 | 5.52 |
| 300.35 | 139.90 | 5.59 |

The same process remained active. No matched Dart error, fatal exception or camera
access exception appeared in the captured process log. Camera FPS reports continued
in every minute; the largest gap between reports was approximately 1.47 seconds.
Initial, middle and final screenshots showed the camera and mock skeleton.

PSS fluctuated between 137.53 and 149.78 MiB and ended below the starting snapshot.
There was no sustained upward trend in these samples; this short test does not
prove absence of a memory leak. Sparse screenshots cannot exclude every brief
visual stall. Slow callback delivery and garbage collection remained observable.
The table's FPS values are **camera callbacks**, not UI FPS.

## 5. Rotation limitation

Forced display rotation and the emulator's virtual physical rotation are separate
controls. Some manual sequences changed the Flutter layout while camera orientation
still reflected the previous direction. Wrong physical/display direction pairing
also produced an artificial upside-down scene.

Both landscape directions showed upright previews when display and physical
rotation were matched and orientation updates arrived. Other return sequences
retained stale camera orientation. Live inspection of the active
`CameraController._value` confirmed disagreement with the displayed orientation;
this was not established solely from screenshots or retained historical values.

The installed CameraX orientation manager samples Android UI orientation on sensor
callbacks, whereas outer app geometry uses `MediaQuery`. Their update timing can
therefore differ during these manual tests. The exact cause of every delayed update
was not isolated. Neither unconditional success on real hardware nor a production
rotation fix is justified by this investigation. Emulator settings were restored;
the app was reopened upright.

## 6. Remaining acceptance checks for the team

1. Run `flutter run --profile -d <physical-android-device-id>`. Record phone model,
   Android/Flutter versions and display refresh rate. Keep camera resolution unchanged.
2. After startup settles, record at least 60 seconds in DevTools Performance with
   mock visible. At a 60 Hz target, review UI and raster timings against the
   approximately 16.67 ms frame budget and inspect slow frames. Do not substitute
   the Camera FPS label for this measurement. Save the trace and observed result.
3. Compare the same scene with mock hidden. Repeat if host/device conditions change;
   decide on further optimization from reproducible measurements.
4. Naturally rotate the phone to both landscape directions and back. Check upright,
   proportionate preview and shared overlay geometry. Check Home/return and sleep/wake.
5. Verify permission denial/recovery and longer operation on the target device.
   Future real-landmark integration must separately validate model-to-preview mapping.

Issue #29 should remain pending until the **60 FPS UI acceptance criterion** is
supported by device evidence. No commit, push, pull request or issue closure was
performed as part of this report.

## 7. Simple explanation for presenting the work

«روی تصویر دوربین یک لایهٔ شفاف گذاشتیم. این لایه شش نقطه و پنج خط را رسم
می‌کند. جای نقطه‌ها را با همان بزرگ‌نمایی و برش تصویر دوربین حساب می‌کنیم.
فعلاً نقطه‌ها فرضی‌اند و حرکتشان برای تست رسم است؛ بدن را تشخیص نمی‌دهند.
تست‌های کد و تست پنج‌دقیقه‌ای ایمولاتور انجام شده، ولی روانی ۶۰ فریم رابط را
هنوز باید روی گوشی واقعی تأیید کنیم.»
