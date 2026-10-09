import 'package:calis_mobile/widgets/skeleton_overlay.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

List<Invocation> drawCalls(TestRecordingCanvas canvas, Symbol method) => canvas
    .invocations
    .map((record) => record.invocation)
    .where((invocation) => invocation.memberName == method)
    .where(
      (invocation) =>
          (invocation.positionalArguments.last as Paint).color.toARGB32() ==
          Colors.green.toARGB32(),
    )
    .toList();

void expectOffset(Offset actual, Offset expected) {
  expect(actual.dx, closeTo(expected.dx, 0.000001));
  expect(actual.dy, closeTo(expected.dy, 0.000001));
}

void main() {
  test('dark outlines sit behind smaller green joints and bones', () {
    final canvas = TestRecordingCanvas();
    SkeletonPainter(
      cameraSize: const Size(100, 100),
      joints: const {'shoulder': Offset(0.2, 0.2), 'elbow': Offset(0.8, 0.8)},
    ).paint(canvas, const Size(100, 100));
    final lines = canvas.invocations
        .map((record) => record.invocation)
        .where((call) => call.memberName == #drawLine)
        .toList();
    expect(lines, hasLength(2));
    final outline = lines[0].positionalArguments.last as Paint;
    final foreground = lines[1].positionalArguments.last as Paint;
    expect(outline.color, Colors.black);
    expect(foreground.color.toARGB32(), Colors.green.toARGB32());
    expect(outline.strokeWidth, greaterThan(foreground.strokeWidth));
    expect(
      lines[0].positionalArguments.take(2),
      lines[1].positionalArguments.take(2),
    );

    final circles = canvas.invocations
        .map((record) => record.invocation)
        .where((call) => call.memberName == #drawCircle)
        .toList();
    expect(circles, hasLength(4));
    for (var i = 0; i < circles.length; i += 2) {
      expect(
        (circles[i].positionalArguments.last as Paint).color,
        Colors.black,
      );
      expect(
        (circles[i + 1].positionalArguments.last as Paint).color.toARGB32(),
        Colors.green.toARGB32(),
      );
      expect(
        circles[i].positionalArguments[0],
        circles[i + 1].positionalArguments[0],
      );
      expect(
        circles[i].positionalArguments[1] as double,
        greaterThan(circles[i + 1].positionalArguments[1] as double),
      );
    }
  });
  group('BoxFit.cover landmark mapping', () {
    // These expected positions are calculated independently by hand.
    final cases = [
      (
        name: 'portrait crops horizontally',
        camera: const Size(720, 1280),
        canvas: const Size(400, 800),
        expected: const [Offset(-25, 0), Offset(200, 400), Offset(425, 800)],
      ),
      (
        name: 'landscape crops vertically',
        camera: const Size(1280, 720),
        canvas: const Size(800, 400),
        expected: const [Offset(0, -25), Offset(400, 200), Offset(800, 425)],
      ),
      (
        name: 'matching aspect ratios need no cropping',
        camera: const Size(1280, 720),
        canvas: const Size(640, 360),
        expected: const [Offset(0, 0), Offset(320, 180), Offset(640, 360)],
      ),
    ];

    for (final scenario in cases) {
      test(scenario.name, () {
        final canvas = TestRecordingCanvas();
        SkeletonPainter(
          cameraSize: scenario.camera,
          joints: const {
            'shoulder': Offset.zero,
            'elbow': Offset(0.5, 0.5),
            'wrist': Offset(1, 1),
          },
        ).paint(canvas, scenario.canvas);

        final circles = drawCalls(canvas, #drawCircle);
        expect(circles, hasLength(3));
        for (var i = 0; i < circles.length; i++) {
          expectOffset(
            circles[i].positionalArguments[0] as Offset,
            scenario.expected[i],
          );
        }

        // Bones must use the same mapped positions as their joints.
        final lines = drawCalls(canvas, #drawLine);
        expect(lines, hasLength(2));
        for (var i = 0; i < lines.length; i++) {
          expectOffset(
            lines[i].positionalArguments[0] as Offset,
            scenario.expected[i],
          );
          expectOffset(
            lines[i].positionalArguments[1] as Offset,
            scenario.expected[i + 1],
          );
        }
      });
    }
  });

  test('missing elbow skips its bones but preserves shoulder to hip', () {
    final canvas = TestRecordingCanvas();
    SkeletonPainter(
      cameraSize: const Size(100, 100),
      joints: const {
        'shoulder': Offset(0.2, 0.2),
        'wrist': Offset(0.8, 0.4),
        'hip': Offset(0.2, 0.6),
      },
    ).paint(canvas, const Size(100, 100));

    expect(drawCalls(canvas, #drawCircle), hasLength(3));
    final lines = drawCalls(canvas, #drawLine);
    expect(lines, hasLength(1));
    expectOffset(
      lines.single.positionalArguments[0] as Offset,
      const Offset(20, 20),
    );
    expectOffset(
      lines.single.positionalArguments[1] as Offset,
      const Offset(20, 60),
    );
  });

  test('empty pose draws no joints or bones', () {
    final canvas = TestRecordingCanvas();
    SkeletonPainter(
      joints: const {},
      cameraSize: const Size(100, 100),
    ).paint(canvas, const Size(100, 100));
    expect(drawCalls(canvas, #drawCircle), isEmpty);
    expect(drawCalls(canvas, #drawLine), isEmpty);
  });

  group('repaint decisions', () {
    final joints = <String, Offset>{'shoulder': const Offset(0.2, 0.3)};
    final original = SkeletonPainter(
      joints: joints,
      cameraSize: const Size(720, 1280),
    );

    test('changed pose requests repaint', () {
      final updated = SkeletonPainter(
        joints: {'shoulder': const Offset(0.4, 0.3)},
        cameraSize: const Size(720, 1280),
      );
      expect(updated.shouldRepaint(original), isTrue);
    });

    test('changed camera dimensions request repaint', () {
      final updated = SkeletonPainter(
        joints: joints,
        cameraSize: const Size(1280, 720),
      );
      expect(updated.shouldRepaint(original), isTrue);
    });

    test('unchanged pose reference and dimensions need no repaint', () {
      final unchanged = SkeletonPainter(
        joints: joints,
        cameraSize: const Size(720, 1280),
      );
      expect(unchanged.shouldRepaint(original), isFalse);
    });
  });
}
