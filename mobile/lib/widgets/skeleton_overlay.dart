import 'package:flutter/material.dart';

import 'dart:math' as math;

class SkeletonOverlay extends StatelessWidget {
  const SkeletonOverlay({
    super.key,
    required this.joints,
    required this.cameraSize,
  });

  final Map<String, Offset> joints;
  final Size cameraSize;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: SkeletonPainter(joints: joints, cameraSize: cameraSize),
      size: Size.infinite,
    );
  }
}

class SkeletonPainter extends CustomPainter {
  SkeletonPainter({
    required this.joints,
    required this.cameraSize,
    super.repaint,
  });

  final Map<String, Offset> joints;
  final Size cameraSize;

  static const List<(String, String)> connections = [
    ('shoulder', 'elbow'),
    ('elbow', 'wrist'),
    ('shoulder', 'hip'),
    ('hip', 'knee'),
    ('knee', 'ankle'),
  ];

  Offset _mapToCanvas(Offset joint, Size canvasSize) {
    final scaleX = canvasSize.width / cameraSize.width;
    final scaleY = canvasSize.height / cameraSize.height;

    // BoxFit.cover uses the larger scale so the whole canvas is covered.
    final scale = math.max(scaleX, scaleY);

    final displayedWidth = cameraSize.width * scale;
    final displayedHeight = cameraSize.height * scale;

    // The excess part of the scaled camera image is cropped equally
    // from both sides because FittedBox centers its child.
    final cropX = (displayedWidth - canvasSize.width) / 2;
    final cropY = (displayedHeight - canvasSize.height) / 2;

    final screenX = joint.dx * cameraSize.width * scale - cropX;
    final screenY = joint.dy * cameraSize.height * scale - cropY;

    return Offset(screenX, screenY);
  }

  @override
  void paint(Canvas canvas, Size size) {
    final jointPaint = Paint()
      ..color = Colors.green
      ..style = PaintingStyle.fill;

    final bonePaint = Paint()
      ..color = Colors.green
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    final boneOutlinePaint = Paint()
      ..color = Colors.black
      ..strokeWidth = 5
      ..style = PaintingStyle.stroke;

    final jointOutlinePaint = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.fill;

    for (final connection in connections) {
      final startJoint = joints[connection.$1];
      final endJoint = joints[connection.$2];

      if (startJoint == null || endJoint == null) {
        continue;
      }

      final start = _mapToCanvas(startJoint, size);

      final end = _mapToCanvas(endJoint, size);
      canvas.drawLine(start, end, boneOutlinePaint);
      canvas.drawLine(start, end, bonePaint);
    }

    for (final joint in joints.values) {
      final position = _mapToCanvas(joint, size);

      canvas.drawCircle(position, 8, jointOutlinePaint);
      canvas.drawCircle(position, 6, jointPaint);
    }
  }

  @override
  bool shouldRepaint(covariant SkeletonPainter oldDelegate) {
    return oldDelegate.joints != joints || oldDelegate.cameraSize != cameraSize;
  }
}
