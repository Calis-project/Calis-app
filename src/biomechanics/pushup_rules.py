import math
from typing import Dict, List, Optional, Tuple, Any

def calculate_angle(p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> float:
    """
    Calculate the 2D angle between three points (p2 is the vertex).
    Returns the angle in degrees [0, 180].
    """
    dx1 = p1[0] - p2[0]
    dy1 = p1[1] - p2[1]
    dx2 = p3[0] - p2[0]
    dy2 = p3[1] - p2[1]

    angle1 = math.atan2(dy1, dx1)
    angle2 = math.atan2(dy2, dx2)
    
    angle = math.degrees(abs(angle1 - angle2))
    if angle > 180.0:
        angle = 360.0 - angle
        
    return angle

def is_hip_sagging(shoulder: Tuple[float, float], hip: Tuple[float, float], ankle: Tuple[float, float]) -> bool:
    """
    Detect if the hip is sagging based on body angle and vertical displacement.
    Uses y-down coordinate system (standard for images/video).
    """
    body_angle = calculate_angle(shoulder, hip, ankle)
    
    if body_angle >= 160.0:
        return False
        
    # Calculate vertical displacement from the shoulder-ankle line
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

def evaluate_pushup_stream(landmarks: List[Optional[Dict[str, Tuple[float, float]]]]) -> Dict[str, Any]:
    """
    Evaluate a stream of landmarks to count pushup reps and detect form errors.
    """
    state = "IDLE"
    rep_count = 0
    detected_error = None
    is_valid = True
    
    for frame in landmarks:
        if frame is None:
            continue
            
        shoulder = frame.get("shoulder")
        elbow = frame.get("elbow")
        wrist = frame.get("wrist")
        hip = frame.get("hip")
        ankle = frame.get("ankle")
        
        if not all([shoulder, elbow, wrist, hip, ankle]):
            continue
            
        # Check for hip sag
        if is_hip_sagging(shoulder, hip, ankle):
            detected_error = "HIP_SAG"
            is_valid = False
            
        elbow_angle = calculate_angle(shoulder, elbow, wrist)
        body_angle = calculate_angle(shoulder, hip, ankle)
        
        is_straight_body = body_angle >= 160.0
        
        # State Machine Transitions
        if state == "IDLE":
            if is_straight_body and elbow_angle > 150.0:
                state = "PLANK"
        
        elif state == "PLANK":
            if elbow_angle < 150.0:
                state = "DESCENDING"
                
        elif state == "DESCENDING":
            if elbow_angle <= 90.0:
                state = "BOTTOM"
            elif elbow_angle > 150.0:
                # Returned to plank without going deep enough
                state = "PLANK"
                
        elif state == "BOTTOM":
            if elbow_angle > 90.0:
                state = "ASCENDING"
                
        elif state == "ASCENDING":
            if elbow_angle > 150.0:
                state = "PLANK"
                rep_count += 1
            elif elbow_angle <= 90.0:
                # Went back down
                state = "BOTTOM"
                
    return {
        "detected_error": detected_error,
        "is_valid": is_valid,
        "rep_count": rep_count,
        "state": state
    }
