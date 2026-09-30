import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/services.dart';

/// Image-relative MediaPipe coordinates and visibility for one body point.
class NormalizedLandmark {
  const NormalizedLandmark({
    required this.x,
    required this.y,
    this.z,
    required this.likelihood,
  });

  final double x;
  final double y;
  final double? z;
  final double likelihood;
}

/// Sends Flutter camera frames to the platform MediaPipe Pose Landmarker.
class PoseLandmarkBridge {
  PoseLandmarkBridge({MethodChannel? channel})
    : _channel = channel ?? const MethodChannel('calis/pose_landmarks');

  final MethodChannel _channel;
  bool _initialized = false;
  int _lastTimestampMs = -1;

  Future<void> initialize() async {
    if (_initialized) return;
    final model = await rootBundle.load('assets/pose_landmarker_lite.task');
    await _channel.invokeMethod<void>(
      'initialize',
      model.buffer.asUint8List(model.offsetInBytes, model.lengthInBytes),
    );
    _initialized = true;
  }

  Future<Map<String, NormalizedLandmark>> detect(
    CameraImage image,
    CameraDescription camera,
    DeviceOrientation deviceOrientation,
    int timestampMs,
  ) async {
    if (!_initialized) throw StateError('MediaPipe has not been initialized.');
    final expectedFormat = Platform.isAndroid
        ? ImageFormatGroup.yuv420
        : ImageFormatGroup.bgra8888;
    final expectedPlanes = Platform.isAndroid ? 3 : 1;
    if (image.format.group != expectedFormat ||
        image.planes.length != expectedPlanes) {
      throw UnsupportedError('Unsupported camera image format or plane count.');
    }

    // MediaPipe VIDEO mode requires monotonically increasing timestamps.
    final monotonicTimestamp = timestampMs > _lastTimestampMs
        ? timestampMs
        : _lastTimestampMs + 1;
    _lastTimestampMs = monotonicTimestamp;
    final raw = await _channel.invokeListMethod<dynamic>('detect', {
      'width': image.width,
      'height': image.height,
      'rotation': _rotationDegrees(camera, deviceOrientation),
      'timestampMs': monotonicTimestamp,
      'planes': [
        for (final plane in image.planes)
          {
            'bytes': plane.bytes,
            'bytesPerRow': plane.bytesPerRow,
            'bytesPerPixel': plane.bytesPerPixel ?? 1,
          },
      ],
    });
    return mapPose(raw ?? const []);
  }

  /// Selects the more visible side, matching src/vision/pose_extractor.py.
  static Map<String, NormalizedLandmark> mapPose(List<dynamic> pose) {
    if (pose.length < 33) return const {};
    const left = [11, 13, 15, 23, 27];
    const right = [12, 14, 16, 24, 28];
    const names = ['shoulder', 'elbow', 'wrist', 'hip', 'ankle'];
    double visibility(int index) =>
        ((pose[index] as Map)['visibility'] as num?)?.toDouble() ?? 0;
    final leftScore = left.fold<double>(0, (sum, i) => sum + visibility(i));
    final rightScore = right.fold<double>(0, (sum, i) => sum + visibility(i));
    final indices = leftScore >= rightScore ? left : right;
    return {
      for (var i = 0; i < names.length; i++)
        names[i]: NormalizedLandmark(
          x: ((pose[indices[i]] as Map)['x'] as num).toDouble(),
          y: ((pose[indices[i]] as Map)['y'] as num).toDouble(),
          z: ((pose[indices[i]] as Map)['z'] as num?)?.toDouble(),
          likelihood: visibility(indices[i]),
        ),
    };
  }

  Future<void> close() async {
    if (!_initialized) return;
    _initialized = false;
    await _channel.invokeMethod<void>('close');
  }

  static int _rotationDegrees(
    CameraDescription camera,
    DeviceOrientation deviceOrientation,
  ) {
    if (Platform.isIOS) return camera.sensorOrientation;
    final deviceDegrees = switch (deviceOrientation) {
      DeviceOrientation.portraitUp => 0,
      DeviceOrientation.landscapeLeft => 90,
      DeviceOrientation.portraitDown => 180,
      DeviceOrientation.landscapeRight => 270,
    };
    return camera.lensDirection == CameraLensDirection.front
        ? (camera.sensorOrientation + deviceDegrees) % 360
        : (camera.sensorOrientation - deviceDegrees + 360) % 360;
  }
}
