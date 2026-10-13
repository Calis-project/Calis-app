import math
from typing import Dict, List, Optional, Tuple, Any

# Temporal confirmation of form errors, in frames
SAG_CONFIRM_FRAMES = 3      # consecutive sag frames before HIP_SAG becomes active
SAG_RECOVERY_FRAMES = 3     # consecutive clean frames before HIP_SAG or TRACKING_LOST clears
TRACKING_LOSS_FRAMES = 15   # consecutive frames without landmarks before the live cue becomes TRACKING_LOST

HIP_SAG = "HIP_SAG"
TRACKING_LOST = "TRACKING_LOST"

_REP_STATES = ("DESCENDING", "BOTTOM", "ASCENDING")

def calculate_angle(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    aspect_ratio: float = 1.0,
) -> float:
    """
    Calculate the 2D angle between three points (p2 is the vertex).

    aspect_ratio is frame width / frame height. MediaPipe normalizes x by the
    frame width and y by the frame height, so normalized points must have x
    rescaled before angles are measured. Leave it at 1.0 only for points that
    already share one unit on both axes (e.g. pixels).

    Returns the angle in degrees [0, 180].
    """
    dx1 = (p1[0] - p2[0]) * aspect_ratio
    dy1 = p1[1] - p2[1]
    dx2 = (p3[0] - p2[0]) * aspect_ratio
    dy2 = p3[1] - p2[1]

    angle1 = math.atan2(dy1, dx1)
    angle2 = math.atan2(dy2, dx2)
    
    angle = math.degrees(abs(angle1 - angle2))
    if angle > 180.0:
        angle = 360.0 - angle
        
    return angle

def is_hip_sagging(
    shoulder: Tuple[float, float],
    hip: Tuple[float, float],
    ankle: Tuple[float, float],
    aspect_ratio: float = 1.0,
) -> bool:
    """
    Detect if the hip is sagging based on body angle and vertical displacement.
    Uses y-down coordinate system (standard for images/video).
    aspect_ratio is frame width / frame height (see calculate_angle).
    """
    body_angle = calculate_angle(shoulder, hip, ankle, aspect_ratio)
    
    if body_angle >= 160.0:
        return False
        
    # Calculate vertical displacement from the shoulder-ankle line.
    # This compares y values at the hip's own x, so its outcome does not depend
    # on how x is scaled and needs no aspect-ratio correction.
    dx = ankle[0] - shoulder[0]
    dy = ankle[1] - shoulder[1]
    
    if abs(dx) < 1e-4:
        expected_y = (shoulder[1] + ankle[1]) / 2.0
    else:
        # expected y on the line at hip's x
        t = (hip[0] - shoulder[0]) / dx
        expected_y = shoulder[1] + t * dy
        
    # In y-down, if hip's y is greater than expected_y, it's sagging (closer to floor)
    return hip[1] > expected_y

class PushupEvaluator:
    """
    Frame-by-frame push-up evaluation: rep counting, live form feedback and error history.

    Feed one landmark frame at a time to update(); every call returns the current result:
      state            movement state: IDLE, PLANK, DESCENDING, BOTTOM or ASCENDING
      rep_count        completed full-depth reps, including reps with a confirmed form error
      detected_error   session history: "HIP_SAG" once a sag has been confirmed, never reset
      is_valid         session history: False once any form error has been confirmed
      current_error    live cue: "HIP_SAG" while a confirmed sag is active, "TRACKING_LOST"
                       while form cannot be assessed, otherwise None
      rep_errors       one entry per classified rep, in order: None, or the error confirmed
                       during it. Entries are only ever appended, never changed.
      valid_rep_count  classified reps without a confirmed error

    Temporal confirmation (the per-frame test is is_hip_sagging):
      - HIP_SAG becomes active after SAG_CONFIRM_FRAMES consecutive sag frames and clears
        after SAG_RECOVERY_FRAMES consecutive clean frames. Shorter runs are ignored.
      - A frame without all five landmarks is UNKNOWN: neither sag nor clean. It restarts
        both a pending confirmation and a pending recovery, so the frames that confirm a
        sag or a recovery are always consecutive observed frames.
      - A cue that is already confirmed is kept through a short dropout. After
        TRACKING_LOSS_FRAMES consecutive unknown frames the cue becomes TRACKING_LOST.
      - When landmarks return, the cue stays TRACKING_LOST until it is verified again:
        SAG_RECOVERY_FRAMES consecutive clean frames give None, SAG_CONFIRM_FRAMES
        consecutive sag frames give HIP_SAG.
      - Session and rep history are never erased, and the movement state is left as it was.

    Rep classification:
      - A frame belongs to a rep while the state is DESCENDING, BOTTOM or ASCENDING
        (from the first frame below lockout to the last frame before lockout).
      - A rep is marked with an error when it contains at least one frame of a confirmed
        sag run, including the frames that led up to the confirmation. A cue that is
        still fading out does not mark a rep that has no sag frame of its own.
      - A rep is counted on its lockout frame and normally classified on that same frame.
        Only when a sag run that began on the rep's last frame is still unconfirmed on
        the lockout frame is the classification held back, and it is settled on the next
        frame. So rep_count - len(rep_errors) is 1 on that single frame and 0 otherwise.
      - If the stream ends on that frame, the rep stays counted but unclassified. A rep
        still in progress when the stream ends is neither counted nor classified.
      - Errors confirmed outside completed reps (plank holds, abandoned shallow attempts,
        a rep still in progress at the end) appear only in detected_error and is_valid.
    """

    def __init__(self, frame_width: float, frame_height: float):
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError(f"Invalid frame size: {frame_width}x{frame_height}")
        self._aspect_ratio = frame_width / frame_height

        self.state = "IDLE"
        self.rep_count = 0
        self.detected_error: Optional[str] = None
        self.is_valid = True
        self.current_error: Optional[str] = None
        self.rep_errors: List[Optional[str]] = []

        self._sag_run = 0        # consecutive sag frames
        self._clean_run = 0      # consecutive clean frames
        self._unknown_run = 0    # consecutive frames without usable landmarks
        self._rep_error: Optional[str] = None    # error confirmed in the rep in progress
        self._rep_pending = False                # last counted rep waits for a sag run to resolve

    def update(self, frame: Optional[Dict[str, Tuple[float, float]]]) -> Dict[str, Any]:
        """Process one frame of landmarks (None when the pose was not detected)."""
        shoulder = elbow = wrist = hip = ankle = None
        if frame is not None:
            shoulder = frame.get("shoulder")
            elbow = frame.get("elbow")
            wrist = frame.get("wrist")
            hip = frame.get("hip")
            ankle = frame.get("ankle")

        if not all([shoulder, elbow, wrist, hip, ankle]):
            self._handle_unknown_frame()
            return self.result()

        self._unknown_run = 0
        elbow_angle = calculate_angle(shoulder, elbow, wrist, self._aspect_ratio)
        body_angle = calculate_angle(shoulder, hip, ankle, self._aspect_ratio)

        self._advance_state(elbow_angle, body_angle >= 160.0)
        if is_hip_sagging(shoulder, hip, ankle, self._aspect_ratio):
            self._handle_sag_frame()
        else:
            self._handle_clean_frame()
        return self.result()

    def result(self) -> Dict[str, Any]:
        return {
            "detected_error": self.detected_error,
            "is_valid": self.is_valid,
            "rep_count": self.rep_count,
            "state": self.state,
            "current_error": self.current_error,
            "rep_errors": list(self.rep_errors),
            "valid_rep_count": self.rep_errors.count(None),
        }

    def _advance_state(self, elbow_angle: float, is_straight_body: bool) -> None:
        # State Machine Transitions
        if self.state == "IDLE":
            if is_straight_body and elbow_angle > 150.0:
                self.state = "PLANK"

        elif self.state == "PLANK":
            if elbow_angle < 150.0:
                self.state = "DESCENDING"

        elif self.state == "DESCENDING":
            if elbow_angle <= 90.0:
                self.state = "BOTTOM"
            elif elbow_angle > 150.0:
                # Returned to plank without going deep enough
                self.state = "PLANK"
                self._rep_error = None

        elif self.state == "BOTTOM":
            if elbow_angle > 90.0:
                self.state = "ASCENDING"

        elif self.state == "ASCENDING":
            if elbow_angle > 150.0:
                self.state = "PLANK"
                self.rep_count += 1
                if self._rep_error is None and self._sag_run > 0:
                    # An unconfirmed sag run reaches the rep's last frame: classify once it resolves
                    self._rep_pending = True
                else:
                    self.rep_errors.append(self._rep_error)
                self._rep_error = None
            elif elbow_angle <= 90.0:
                # Went back down
                self.state = "BOTTOM"

    def _handle_sag_frame(self) -> None:
        self._clean_run = 0
        self._sag_run += 1
        if self._sag_run < SAG_CONFIRM_FRAMES:
            return

        self.current_error = HIP_SAG
        self.detected_error = HIP_SAG
        self.is_valid = False
        if self.state in _REP_STATES:
            self._rep_error = HIP_SAG
        if self._rep_pending:
            self.rep_errors.append(HIP_SAG)
            self._rep_pending = False

    def _handle_clean_frame(self) -> None:
        self._end_sag_run()
        self._clean_run += 1
        if self.current_error is not None and self._clean_run >= SAG_RECOVERY_FRAMES:
            self.current_error = None

    def _handle_unknown_frame(self) -> None:
        # No evidence either way: a pending confirmation and a pending recovery both start over
        self._end_sag_run()
        self._clean_run = 0
        self._unknown_run += 1
        if self._unknown_run >= TRACKING_LOSS_FRAMES:
            self.current_error = TRACKING_LOST

    def _end_sag_run(self) -> None:
        self._sag_run = 0
        if self._rep_pending:
            # The sag that began at the end of the last counted rep was never confirmed
            self.rep_errors.append(None)
            self._rep_pending = False


def evaluate_pushup_stream(
    landmarks: List[Optional[Dict[str, Tuple[float, float]]]],
    frame_width: float,
    frame_height: float,
) -> Dict[str, Any]:
    """
    Evaluate a stream of landmarks to count pushup reps and detect form errors.

    landmarks are MediaPipe-normalized (x, y) points. frame_width and
    frame_height are the dimensions of the frames they were extracted from,
    needed to measure angles without aspect-ratio distortion.

    Returns the PushupEvaluator result after the last frame.
    """
    evaluator = PushupEvaluator(frame_width, frame_height)
    for frame in landmarks:
        evaluator.update(frame)
    return evaluator.result()
