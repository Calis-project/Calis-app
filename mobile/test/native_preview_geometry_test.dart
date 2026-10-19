import 'package:calis_mobile/core/pose_landmark_bridge.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'normalized points rotate with the preview, not just its dimensions',
    () {
      const point = Offset(0.2, 0.3);
      expect(NativeCameraInfo.rotatePoint(point, 0), point);
      expect(NativeCameraInfo.rotatePoint(point, 90), const Offset(0.7, 0.2));
      expect(NativeCameraInfo.rotatePoint(point, 180), const Offset(0.8, 0.7));
      expect(NativeCameraInfo.rotatePoint(point, 270), const Offset(0.3, 0.8));
    },
  );
  // Phone sensors are commonly 90 degrees; tablets may use 0 degrees.
  for (final sensor in [0, 90]) {
    for (var display = 0; display < 4; display++) {
      test('sensor $sensor display $display uses camera geometry', () {
        final info = NativeCameraInfo(
          textureId: 1,
          width: 1280,
          height: 720,
          sensorRotation: sensor,
          displayRotation: display,
        );
        final relativeRotation = (sensor - display * 90 + 360) % 360;
        expect(
          info.displaySize,
          relativeRotation % 180 == 0
              ? const Size(1280, 720)
              : const Size(720, 1280),
        );
        // The texture already contains the sensor transform.
        expect(info.textureQuarterTurns, [0, 1, 2, 3][display]);
      });
    }
  }
}
