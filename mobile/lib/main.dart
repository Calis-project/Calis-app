import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:calis_mobile/core/pose_landmark_bridge.dart';

import 'widgets/pose_overlay.dart';
import 'widgets/mock_skeleton_overlay.dart';

// Run the issue #29 graphics check without loading pose inference.
const _useMockPose = bool.fromEnvironment('SKELETON_MOCK');

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
  // Latest detected joints; an empty map removes the previous skeleton.
  final _liveJoints = ValueNotifier<Map<String, Offset>>({});
  CameraController? _controller;
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
  String _frameSize = '';
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
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      if (!_useMockPose) await _poseBridge.initialize();
      if (!mounted) return;

      // Keep the same CameraPreview path verified on the tablet in mock mode.
      final controller = CameraController(
        widget.camera,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: Platform.isAndroid
            ? ImageFormatGroup.yuv420
            : ImageFormatGroup.bgra8888,
      );
      _controller = controller;
      await controller.initialize();
      if (!mounted) return;

      _stopwatch.start();
      await controller.startImageStream((CameraImage image) {
        if (!mounted) return;
        _frameSize = '${image.width}x${image.height}';
        final currentTimestamp = _stopwatch.elapsedMilliseconds;

        if (_lastFrameTimestamp != null) {
          final frameInterval = currentTimestamp - _lastFrameTimestamp!;
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
            'Camera FPS: ${_fps.toStringAsFixed(1)} ($_frameSize) | '
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
          _fpsWindowStart = currentTimestamp;
        }

        if (_useMockPose || _poseError != null) return;
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
    _frameSize = '${image.width}x${image.height}';
    final timer = Stopwatch()..start();
    try {
      final landmarks = await _poseBridge.detect(
        image,
        widget.camera,
        _controller!.value.deviceOrientation,
        _stopwatch.elapsedMilliseconds,
      );
      if (!mounted) return;
      _updateLivePose(landmarks);
      _processedFrames++;
      _landmarkCount = landmarks.length;
      if (landmarks.length == 6) _framesWithLandmarks++;
    } catch (error) {
      debugPrint('Pose detection stopped: $error');
      if (mounted) {
        _liveJoints.value = {};
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
    try {
      if (_controller?.value.isStreamingImages ?? false) {
        await _controller!.stopImageStream();
      }
    } catch (error) {
      debugPrint('Camera stream cleanup failed: $error');
    } finally {
      if (_inFlightFrame != null) await _inFlightFrame;
      await _poseBridge.close();
      try {
        await _controller?.dispose();
      } catch (error) {
        debugPrint('Camera dispose failed: $error');
      }
    }
  }

  @override
  void dispose() {
    _liveJoints.dispose();
    _stopwatch.stop();
    unawaited(_disposeCamera());
    super.dispose();
  }

  void _updateLivePose(
    Map<String, NormalizedLandmark> landmarks, {
    int rotation = 0,
  }) {
    // The painter needs only each joint's name and normalized x/y position.
    _liveJoints.value = {
      for (final entry in landmarks.entries)
        entry.key: NativeCameraInfo.rotatePoint(
          Offset(entry.value.x, entry.value.y),
          rotation,
        ),
    };
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Scaffold(body: Center(child: Text('Camera error: $_error')));
    }

    final isControllerReady =
        _controller != null && _controller!.value.isInitialized;

    if (!isControllerReady) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final width = _controller!.value.previewSize!.width;
    final height = _controller!.value.previewSize!.height;

    final landscape =
        MediaQuery.orientationOf(context) == Orientation.landscape;

    final cameraSize = Size(
      landscape ? width : height,
      landscape ? height : width,
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
                width: cameraSize.width,
                height: cameraSize.height,
                child: CameraPreview(_controller!),
              ),
            ),
          ),

          if (_useMockPose)
            MockSkeletonOverlay(cameraSize: cameraSize)
          else
            PoseOverlay(liveJoints: _liveJoints, cameraSize: cameraSize),

          Positioned(
            top: 40,
            left: 16,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Camera: ${_fps.toStringAsFixed(1)} FPS ($_frameSize)',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                if (_useMockPose)
                  const Text(
                    'Mock UI test — synthetic points',
                    style: TextStyle(color: Colors.white),
                  ),
                Text(
                  'Landmarks: ${_poseFps.toStringAsFixed(1)} FPS '
                  '($_landmarkCount joints)',
                  style: const TextStyle(color: Colors.white),
                ),
                if (!_useMockPose)
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
