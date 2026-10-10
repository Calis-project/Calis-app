import 'package:calis_mobile/core/pose_landmark_bridge.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('selects the visible MediaPipe side and matches Python joint names', () {
    final pose = List.generate(
      33,
      (index) => <String, double>{
        'x': index / 100,
        'y': index / 200,
        'z': -0.1,
        'visibility': index.isOdd ? 0.9 : 0.1,
      },
    );

    final joints = PoseLandmarkBridge.mapPose(pose);

    expect(joints.keys, ['shoulder', 'elbow', 'wrist', 'hip', 'ankle']);
    expect(joints['shoulder']!.x, 0.11);
    expect(joints['elbow']!.x, 0.13);
    expect(joints['wrist']!.x, 0.15);
    expect(joints['hip']!.x, 0.23);
    expect(joints['ankle']!.x, 0.27);
    expect(joints['shoulder']!.likelihood, 0.9);
    expect(joints['shoulder']!.z, -0.1);
    expect(PoseLandmarkBridge.mapPose([]), isEmpty);
  });

  test('supports nullable z coordinates in NormalizedLandmark and mapPose', () {
    const landmark = NormalizedLandmark(x: 0.5, y: 0.5, likelihood: 0.8);
    expect(landmark.z, isNull);

    final poseWithoutZ = List.generate(
      33,
      (index) => <String, dynamic>{
        'x': 0.2,
        'y': 0.3,
        'visibility': 0.9,
      },
    );
    final joints = PoseLandmarkBridge.mapPose(poseWithoutZ);
    expect(joints['shoulder']!.z, isNull);
  });

  test('PoseDetectionEvent retains cameraFrameCount and detection fields', () {
    const event = PoseDetectionEvent(
      landmarks: {},
      latencyMs: 24,
      width: 1280,
      height: 720,
      rotation: 90,
      cameraFrameCount: 42,
    );
    expect(event.cameraFrameCount, 42);
    expect(event.latencyMs, 24);
    expect(event.width, 1280);
    expect(event.height, 720);
    expect(event.rotation, 90);
  });
}
