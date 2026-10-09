import 'package:flutter/material.dart';
import 'package:camera/camera.dart';

import 'widgets/skeleton_overlay.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    final cameras = await availableCameras();
    debugPrint('Available cameras: ${cameras.length}');
    final backCamera = cameras.firstWhere(
      (camera) => camera.lensDirection == CameraLensDirection.back,
      orElse: () => throw CameraException(
        'NoBackCamera',
        'No back camera is available on this device.',
      ),
    );

    runApp(CalisApp(camera: backCamera));
  } on CameraException catch (error) {
    runApp(
      MaterialApp(
        home: Scaffold(
          body: Center(
            child: Text('Camera error: ${error.description ?? error.code}'),
          ),
        ),
      ),
    );
  }
}

class CalisApp extends StatelessWidget {
  const CalisApp({super.key, required this.camera});

  final CameraDescription camera;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: CameraScreen(camera: camera),
    );
  }
}

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key, required this.camera});

  final CameraDescription camera;

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _mockAnimation;
  bool _showMock = true;
  late CameraController _controller;
  int _frameCount = 0;
  double _fps = 0.0;
  final Stopwatch _stopwatch = Stopwatch();
  int? _lastFrameTimestamp;
  int _fpsWindowStart = 0;
  String? _error;

  @override
  void initState() {
    super.initState();
    _mockAnimation = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _controller = CameraController(
      widget.camera,
      ResolutionPreset.high,
      enableAudio: false,
    );
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      await _controller.initialize();
      if (!mounted) return;

      _stopwatch.start();
      await _controller.startImageStream((CameraImage image) {
        if (!mounted) return;
        final currentTimestamp = _stopwatch.elapsedMilliseconds;

        if (_lastFrameTimestamp != null) {
          final frameInterval = currentTimestamp - _lastFrameTimestamp!;
          // Diagnostic only: a long interval does not prove a dropped frame.
          if (frameInterval > 100) {
            debugPrint('Long frame interval (diagnostic): $frameInterval ms');
          }
        }
        _lastFrameTimestamp = currentTimestamp;
        _frameCount++;

        final elapsedSeconds = (currentTimestamp - _fpsWindowStart) / 1000.0;
        if (elapsedSeconds >= 1.0) {
          setState(() {
            _fps = _frameCount / elapsedSeconds;
          });
          debugPrint('Camera stream FPS: ${_fps.toStringAsFixed(1)}');
          _frameCount = 0;
          // Keep the clock continuous so frame intervals remain comparable.
          _fpsWindowStart = currentTimestamp;
        }
      });

      if (!mounted) return;
      setState(() {});
    } on CameraException catch (error) {
      _stopwatch.stop();
      await _disposeCamera();
      if (!mounted) return;
      setState(
        () => _error =
            '${error.code}: ${error.description ?? 'Camera initialization failed.'}',
      );
    }
  }

  Future<void> _disposeCamera() async {
    // camera 0.12.1 dispose() does not cancel the Dart image subscription.
    try {
      if (_controller.value.isStreamingImages) {
        await _controller.stopImageStream();
      }
    } catch (error) {
      debugPrint('Camera stream cleanup failed: $error');
    } finally {
      try {
        await _controller.dispose();
      } catch (error) {
        debugPrint('Camera disposal failed: $error');
      }
    }
  }

  @override
  void dispose() {
    _mockAnimation.dispose();
    _stopwatch.stop();
    _disposeCamera();
    super.dispose();
  }

  void _toggleMock() {
    setState(() => _showMock = !_showMock);
    if (_showMock) {
      _mockAnimation.repeat(reverse: true);
    } else {
      _mockAnimation.stop();
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Scaffold(body: Center(child: Text('Camera error: $_error')));
    }
    if (!_controller.value.isInitialized) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final previewSize = _controller.value.previewSize!;

    final landscape =
        MediaQuery.orientationOf(context) == Orientation.landscape;

    final cameraSize = Size(
      landscape ? previewSize.width : previewSize.height,
      landscape ? previewSize.height : previewSize.width,
    );

    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Fill the screen without stretching the camera image.
          ClipRect(
            child: FittedBox(
              fit: BoxFit.cover,
              child: SizedBox(
                width: landscape ? previewSize.width : previewSize.height,
                height: landscape ? previewSize.height : previewSize.width,
                child: CameraPreview(_controller),
              ),
            ),
          ),

          if (_showMock)
            AnimatedBuilder(
              animation: _mockAnimation,
              builder: (context, child) {
                final shift = (_mockAnimation.value - 0.5) * 0.1;

                return SkeletonOverlay(
                  cameraSize: cameraSize,
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

          Positioned(
            top: 40,
            left: 16,
            child: Text(
              'Camera FPS: ${_fps.toStringAsFixed(1)}',
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ),
          Positioned(
            left: 16,
            right: 16,
            bottom: 16,
            child: SafeArea(
              top: false,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 8,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.black87,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      _showMock ? 'Mock pose' : 'Mock pose hidden',
                      style: const TextStyle(color: Colors.white),
                    ),
                  ),
                  FilledButton(
                    onPressed: _toggleMock,
                    child: Text(_showMock ? 'Hide mock' : 'Show mock'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
