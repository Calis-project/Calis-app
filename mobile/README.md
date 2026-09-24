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

There is no automatic background/resume recovery or Retry UI. Restart the app for
a fresh foreground session or after changing permissions. Use an emulator for
functional checks and a physical Android device for performance acceptance.

## Documentation

- [Engineering report and physical-device test protocol](../docs/Arash/flutter_camera_report.md)
- [Simple explanation for learning and presenting the task](../docs/Arash/flutter_camera_explained.md)

Generated platform scaffolding is retained. Android is the current test target;
other platform behavior is not validated by this task.
