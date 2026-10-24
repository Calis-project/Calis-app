import 'package:calis_mobile/widgets/pose_overlay.dart';
import 'package:calis_mobile/widgets/skeleton_overlay.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('live pose updates and empty detection clears old joints', (
    tester,
  ) async {
    final joints = ValueNotifier<Map<String, Offset>>({});
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PoseOverlay(
            liveJoints: joints,
            cameraSize: const Size(720, 1280),
          ),
        ),
      ),
    );
    expect(find.text('No pose detected'), findsOneWidget);
    expect(find.text('Use mock'), findsNothing);
    expect(find.text('Use live'), findsNothing);
    joints.value = {'knee': const Offset(0.3, 0.6)};
    await tester.pump();
    expect(
      tester
          .widget<SkeletonOverlay>(find.byType(SkeletonOverlay))
          .joints['knee'],
      const Offset(0.3, 0.6),
    );
    expect(find.text('Live pose'), findsOneWidget);
    joints.value = {};
    await tester.pump();
    expect(
      tester.widget<SkeletonOverlay>(find.byType(SkeletonOverlay)).joints,
      isEmpty,
    );
    await tester.pumpWidget(const SizedBox());
    joints.dispose();
  });
}
