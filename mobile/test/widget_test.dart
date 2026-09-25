import 'package:calis_mobile/main.dart' as app;
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('plugins.flutter.io/camera');
  final messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;

  tearDown(() => messenger.setMockMethodCallHandler(channel, null));

  for (final hasFrontCamera in [false, true]) {
    testWidgets(
      hasFrontCamera
          ? 'front-only device explains missing back camera'
          : 'no cameras produces a visible error',
      (tester) async {
        messenger.setMockMethodCallHandler(channel, (call) async {
          if (call.method != 'availableCameras') throw MissingPluginException();
          return hasFrontCamera
              ? [
                  {
                    'name': 'front',
                    'lensFacing': 'front',
                    'sensorOrientation': 90,
                  },
                ]
              : [];
        });
        await app.main();
        await tester.pumpAndSettle();
        expect(find.textContaining('No back camera'), findsOneWidget);
      },
    );
  }

  testWidgets('camera enumeration exception produces a visible error', (
    tester,
  ) async {
    messenger.setMockMethodCallHandler(channel, (call) async {
      throw PlatformException(
        code: 'CameraUnavailable',
        message: 'Camera is busy',
      );
    });
    await app.main();
    await tester.pumpAndSettle();
    expect(find.textContaining('Camera is busy'), findsOneWidget);
  });
}
