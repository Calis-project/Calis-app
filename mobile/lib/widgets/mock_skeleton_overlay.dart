import 'package:flutter/material.dart';

import 'skeleton_overlay.dart';

// Issue #29 acceptance fixture. Enabled only by the SKELETON_MOCK build flag.
class MockSkeletonOverlay extends StatefulWidget {
  const MockSkeletonOverlay({super.key, required this.cameraSize});

  final Size cameraSize;

  @override
  State<MockSkeletonOverlay> createState() => _MockSkeletonOverlayState();
}

class _MockSkeletonOverlayState extends State<MockSkeletonOverlay>
    with SingleTickerProviderStateMixin {
  late final AnimationController _animation;

  @override
  void initState() {
    super.initState();
    // Follow display ticks; camera frame rate does not drive this animation.
    _animation = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _animation.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => IgnorePointer(
    child: ClipRect(
      child: AnimatedBuilder(
        animation: _animation,
        builder: (context, child) {
          final shift = (_animation.value - 0.5) * 0.1;
          // Rebuild only the drawing, keeping CameraPreview outside this builder.
          return SkeletonOverlay(
            cameraSize: widget.cameraSize,
            joints: {
              'shoulder': Offset(0.45 + shift, 0.25),
              'elbow': Offset(0.55 + shift, 0.38),
              'wrist': Offset(0.60 + shift, 0.52),
              'hip': Offset(0.48 + shift, 0.50),
              'knee': Offset(0.52 + shift, 0.68),
              'ankle': Offset(0.55 + shift, 0.85),
            },
          );
        },
      ),
    ),
  );
}
