import 'package:calis_mobile/widgets/mock_skeleton_overlay.dart';
import 'package:calis_mobile/widgets/skeleton_overlay.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('mock moves six normalized joints without live detection', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: MockSkeletonOverlay(cameraSize: Size(720, 1280))),
      ),
    );
    final first = tester.widget<SkeletonOverlay>(find.byType(SkeletonOverlay));
    expect(first.joints.keys, [
      'shoulder',
      'elbow',
      'wrist',
      'hip',
      'knee',
      'ankle',
    ]);
    expect(first.cameraSize, const Size(720, 1280));
    await tester.pump(const Duration(milliseconds: 500));
    final second = tester.widget<SkeletonOverlay>(find.byType(SkeletonOverlay));
    expect(second.joints['shoulder'], isNot(first.joints['shoulder']));
    for (final point in second.joints.values) {
      expect(point.dx, inInclusiveRange(0, 1));
      expect(point.dy, inInclusiveRange(0, 1));
    }
    expect(find.byType(FilledButton), findsNothing);
    await tester.pumpWidget(const SizedBox());
    expect(tester.takeException(), isNull);
  });
}
