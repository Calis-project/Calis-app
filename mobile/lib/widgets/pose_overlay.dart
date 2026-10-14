import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import 'skeleton_overlay.dart';

// Shows only the latest real detections over the camera.
class PoseOverlay extends StatelessWidget {
  const PoseOverlay({
    super.key,
    required this.liveJoints,
    required this.cameraSize,
  });

  final ValueListenable<Map<String, Offset>> liveJoints;
  final Size cameraSize;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<Map<String, Offset>>(
      // Update the overlay without rebuilding the camera preview.
      valueListenable: liveJoints,
      builder: (context, joints, child) => Stack(
        fit: StackFit.expand,
        children: [
          // The drawing must not block touches on the screen.
          IgnorePointer(
            child: ClipRect(
              child: SkeletonOverlay(cameraSize: cameraSize, joints: joints),
            ),
          ),
          Positioned(
            left: 16,
            bottom: 16,
            child: SafeArea(
              top: false,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: Colors.black87,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  joints.isEmpty ? 'No pose detected' : 'Live pose',
                  style: const TextStyle(color: Colors.white),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
