import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:calis_mobile/core/pose_landmark_bridge.dart';

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

class _CameraScreenState extends State<CameraScreen> {
  late CameraController _controller;
  final PoseLandmarkBridge _poseBridge = PoseLandmarkBridge();
  int _frameCount = 0;
  double _fps = 0.0;
  double _poseFps = 0.0;
  int _processedFrames = 0;
  int _framesWithLandmarks = 0;
  int _skippedFrames = 0;
  int _lastSkippedFrames = 0;
  int _landmarkCount = 0;
  int _totalProcessingMs = 0;
  int _maxProcessingMs = 0;
  bool _poseBusy = false;
  String? _poseError;
  Future<void>? _inFlightFrame;
  Future<void>? _cameraDisposal;
  final Stopwatch _stopwatch = Stopwatch();
  int? _lastFrameTimestamp;
  int _fpsWindowStart = 0;
  String? _error;

  @override
  void initState() {
    super.initState();

    _controller = CameraController(
      widget.camera,
      ResolutionPreset.medium,
      enableAudio: false,
      imageFormatGroup: Platform.isAndroid
          ? ImageFormatGroup.yuv420
          : ImageFormatGroup.bgra8888,
    );
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      await _controller.initialize();
      if (!mounted) return;
      await _poseBridge.initialize();
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
            _poseFps = _framesWithLandmarks / elapsedSeconds;
            _lastSkippedFrames = _skippedFrames;
          });
          final averageMs = _processedFrames == 0
              ? 0.0
              : _totalProcessingMs / _processedFrames;
          debugPrint(
            'Camera FPS: ${_fps.toStringAsFixed(1)} | '
            'pose frames: $_processedFrames | '
            'landmark FPS: ${_poseFps.toStringAsFixed(1)} | '
            'skipped while busy: $_skippedFrames | '
            'pose ms avg/max: ${averageMs.toStringAsFixed(1)}/$_maxProcessingMs',
          );
          _frameCount = 0;
          _processedFrames = 0;
          _framesWithLandmarks = 0;
          _skippedFrames = 0;
          _totalProcessingMs = 0;
          _maxProcessingMs = 0;
          // Keep the clock continuous so frame intervals remain comparable.
          _fpsWindowStart = currentTimestamp;
        }

        if (_poseError != null) return;
        if (_poseBusy) {
          _skippedFrames++;
          return;
        }
        _poseBusy = true;
        _inFlightFrame = _processFrame(image);
      });

      if (!mounted) return;
      setState(() {});
    } catch (error) {
      _stopwatch.stop();
      await _disposeCamera();
      if (!mounted) return;
      setState(() => _error = error.toString());
    }
  }

  Future<void> _processFrame(CameraImage image) async {
    final timer = Stopwatch()..start();
    try {
      final landmarks = await _poseBridge.detect(
        image,
        widget.camera,
        _controller.value.deviceOrientation,
        _stopwatch.elapsedMilliseconds,
      );
      _processedFrames++;
      _landmarkCount = landmarks.length;
      if (landmarks.length == 5) _framesWithLandmarks++;
    } catch (error) {
      debugPrint('Pose detection stopped: $error');
      if (mounted) {
        setState(() => _poseError = error.toString());
      } else {
        _poseError = error.toString();
      }
    } finally {
      timer.stop();
      _totalProcessingMs += timer.elapsedMilliseconds;
      if (timer.elapsedMilliseconds > _maxProcessingMs) {
        _maxProcessingMs = timer.elapsedMilliseconds;
      }
      _poseBusy = false;
    }
  }

  Future<void> _disposeCamera() => _cameraDisposal ??= _disposeCameraOnce();

  Future<void> _disposeCameraOnce() async {
    // camera 0.12.1 dispose() does not cancel the Dart image subscription.
    try {
      if (_controller.value.isStreamingImages) {
        await _controller.stopImageStream();
      }
    } catch (error) {
      debugPrint('Camera stream cleanup failed: $error');
    } finally {
      if (_inFlightFrame != null) await _inFlightFrame;
      await _poseBridge.close();
      try {
        await _controller.dispose();
      } catch (error) {
        debugPrint('Camera disposal failed: $error');
      }
    }
  }

  @override
  void dispose() {
    _stopwatch.stop();
    unawaited(_disposeCamera());
    super.dispose();
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
          Positioned(
            top: 40,
            left: 16,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Camera: ${_fps.toStringAsFixed(1)} FPS',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                Text(
                  'Landmarks: ${_poseFps.toStringAsFixed(1)} FPS '
                  '($_landmarkCount joints)',
                  style: const TextStyle(color: Colors.white),
                ),
                Text(
                  'Skipped while busy: $_lastSkippedFrames',
                  style: const TextStyle(color: Colors.white),
                ),
                if (_poseError != null)
                  Text(
                    'Pose error: $_poseError',
                    style: const TextStyle(color: Colors.redAccent),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
