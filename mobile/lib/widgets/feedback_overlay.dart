// mobile/lib/widgets/feedback_overlay.dart
//
// TSK-204: Dynamic UI Banners & Audio Cue Triggers
//
// Renders a corrective status banner over the camera preview and plays a
// short audio cue when a biomechanical error becomes active, per
// feedback_schema.json.
//
// NOTE: as of this schema version, the engine (pushup.py) emits one
// FeedbackMessage per evaluated *clip*, not one per frame, and NO_REP_DEPTH
// is not yet set anywhere in the engine (see cues_matrix.md §4). This widget
// is built against the schema's Stream<FeedbackMessage> contract on purpose,
// so it does not care whether that stream is fed by a real per-frame engine
// or a single clip-summary event -- it reacts correctly either way, and will
// need no changes once the engine moves to per-frame emission.
//
// Dependency: add `audioplayers: ^6.0.0` to mobile/pubspec.yaml, and declare
// the two asset files below under `flutter: assets:`.

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';

/// Mirrors the `state` enum in feedback_schema.json.
enum PushupState { idle, plank, descending, bottom, ascending }

/// Mirrors the `error_code` enum in feedback_schema.json.
enum FeedbackErrorCode { none, hipSag, noRepDepth }

PushupState _stateFromJson(String value) {
  switch (value) {
    case 'IDLE':
      return PushupState.idle;
    case 'PLANK':
      return PushupState.plank;
    case 'DESCENDING':
      return PushupState.descending;
    case 'BOTTOM':
      return PushupState.bottom;
    case 'ASCENDING':
      return PushupState.ascending;
  }
  throw FormatException('Unknown state: $value');
}

FeedbackErrorCode _errorCodeFromJson(String value) {
  switch (value) {
    case 'NONE':
      return FeedbackErrorCode.none;
    case 'HIP_SAG':
      return FeedbackErrorCode.hipSag;
    case 'NO_REP_DEPTH':
      return FeedbackErrorCode.noRepDepth;
  }
  throw FormatException('Unknown error_code: $value');
}

/// Dart model for the `FeedbackMessage` object defined in
/// feedback_schema.json. Keep this in sync with that file.
@immutable
class FeedbackMessage {
  const FeedbackMessage({
    required this.repCount,
    required this.state,
    required this.isValid,
    required this.errorCode,
    required this.cueText,
  });

  final int repCount;
  final PushupState state;
  final bool isValid;
  final FeedbackErrorCode errorCode;
  final String cueText;

  factory FeedbackMessage.fromJson(Map<String, dynamic> json) {
    return FeedbackMessage(
      repCount: json['rep_count'] as int,
      state: _stateFromJson(json['state'] as String),
      isValid: json['is_valid'] as bool,
      errorCode: _errorCodeFromJson(json['error_code'] as String),
      cueText: json['cue_text'] as String,
    );
  }

  static const good = FeedbackMessage(
    repCount: 0,
    state: PushupState.idle,
    isValid: true,
    errorCode: FeedbackErrorCode.none,
    cueText: 'Good form',
  );
}

/// Per-error-code presentation config. Extend this map, not the widget body,
/// when new codes (HIP_PIKE, PARTIAL_LOCKOUT, ...) are added in a later
/// schema version.
class _FeedbackVisuals {
  const _FeedbackVisuals({
    required this.color,
    required this.icon,
    this.audioAsset,
  });

  final Color color;
  final IconData icon;
  final String? audioAsset; // null = no sound for this code

  static const _map = <FeedbackErrorCode, _FeedbackVisuals>{
    FeedbackErrorCode.none: _FeedbackVisuals(
      color: Colors.green,
      icon: Icons.check_circle,
    ),
    FeedbackErrorCode.hipSag: _FeedbackVisuals(
      color: Colors.red,
      icon: Icons.warning_rounded,
      audioAsset: 'audio/hip_sag.mp3',
    ),
    FeedbackErrorCode.noRepDepth: _FeedbackVisuals(
      color: Colors.red,
      icon: Icons.warning_rounded,
      audioAsset: 'audio/no_rep_depth.mp3',
    ),
  };

  static _FeedbackVisuals of(FeedbackErrorCode code) => _map[code]!;
}

/// Status banner + audio cue overlay. Place this in a [Stack] above your
/// [CameraPreview].
///
/// Feed it a [feedbackStream] of [FeedbackMessage]s -- in production this
/// will eventually come from the Dart/C++ bridge to the pose engine; today
/// it can be any Stream<FeedbackMessage>, including a fake one in tests.
class FeedbackOverlay extends StatefulWidget {
  const FeedbackOverlay({super.key, required this.feedbackStream});

  final Stream<FeedbackMessage> feedbackStream;

  @override
  State<FeedbackOverlay> createState() => _FeedbackOverlayState();
}

class _FeedbackOverlayState extends State<FeedbackOverlay> {
  FeedbackMessage _current = FeedbackMessage.good;
  StreamSubscription<FeedbackMessage>? _subscription;
  final AudioPlayer _audioPlayer = AudioPlayer();

  @override
  void initState() {
    super.initState();
    _subscription = widget.feedbackStream.listen(_onMessage);
  }

  void _onMessage(FeedbackMessage message) {
    final codeChanged = message.errorCode != _current.errorCode;

    // Update the banner immediately -- this is the only thing the <200ms
    // DoD is measuring, so it must never wait on the audio call below.
    setState(() => _current = message);

    // Fire the cue only on the rising edge (code just became active), not on
    // every message that happens to repeat the same active error. This is
    // what stops a repeated/duplicate clip-summary -- or, later, a run of
    // per-frame messages -- from machine-gunning the beep.
    if (codeChanged && message.errorCode != FeedbackErrorCode.none) {
      final asset = _FeedbackVisuals.of(message.errorCode).audioAsset;
      if (asset != null) {
        // Fire-and-forget: never await audio playback before the UI update
        // above, and never let a playback error crash the overlay.
        unawaited(
          _audioPlayer.play(AssetSource(asset)).catchError((_) {}),
        );
      }
    }
  }

  @override
  void dispose() {
    _subscription?.cancel();
    _audioPlayer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final visuals = _FeedbackVisuals.of(_current.errorCode);

    return Positioned(
      top: 40,
      left: 16,
      right: 16,
      child: AnimatedSwitcher(
        // Well under the 200ms budget so the transition itself never eats
        // into the DoD's timing allowance.
        duration: const Duration(milliseconds: 120),
        child: Container(
          key: ValueKey(_current.errorCode),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(
            color: visuals.color.withOpacity(0.92),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(visuals.icon, color: Colors.white),
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  _current.cueText,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
