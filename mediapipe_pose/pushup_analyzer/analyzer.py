import os
import sys
import json
import argparse
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Define Paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
MODEL_PATH = os.path.join(PARENT_DIR, "pose_landmarker_heavy.task")
INPUT_DIR = os.path.join(PARENT_DIR, "data", "input")
OUTPUT_DIR = os.path.join(PARENT_DIR, "data", "output")

# Landmark index names for reference
LANDMARKS = {
    "L_SHOULDER": 11, "R_SHOULDER": 12,
    "L_ELBOW": 13, "R_ELBOW": 14,
    "L_WRIST": 15, "R_WRIST": 16,
    "L_HIP": 23, "R_HIP": 24,
    "L_KNEE": 25, "R_KNEE": 26,
    "L_ANKLE": 27, "R_ANKLE": 28
}

class PushupStateTracker:
    def __init__(self):
        self.rep_count = 0
        self.good_reps = 0
        self.shallow_reps = 0
        self.state = "UP"  # UP, DESCENT, BOTTOM, ASCENT
        self.min_elbow_angle = 180.0
        self.elbow_straight_baseline = 165.0
        
        # Form violation tracking for current rep
        self.current_rep_violations = {
            "hip_sagging": False,
            "hip_piking": False,
            "bent_knees": False
        }
        
        # History of completed reps
        self.reps_history = []
        
        # Active form violations in the current frame
        self.active_violations = {
            "hip_sagging": False,
            "hip_piking": False,
            "bent_knees": False
        }
        
        # For dynamic calibration
        self.elbow_angle_history = []

    def update(self, elbow_angle, hip_angle, knee_angle):
        self.elbow_angle_history.append(elbow_angle)
        if len(self.elbow_angle_history) > 100:
            self.elbow_angle_history.pop(0)
            
        # Update baseline using maximum elbow angle seen during UP state
        if self.state == "UP":
            self.elbow_straight_baseline = max(self.elbow_straight_baseline, elbow_angle)
            
        up_threshold = self.elbow_straight_baseline - 20.0  # e.g., 145° if baseline is 165°
        
        # Active violations checks
        # Spine alignment: normal hip angle is close to 180°.
        if hip_angle < 155.0:
            self.active_violations["hip_sagging"] = True
            self.active_violations["hip_piking"] = False
        elif hip_angle > 195.0:
            self.active_violations["hip_sagging"] = False
            self.active_violations["hip_piking"] = True
        else:
            self.active_violations["hip_sagging"] = False
            self.active_violations["hip_piking"] = False
            
        # Knee flexion check
        if knee_angle < 162.0:
            self.active_violations["bent_knees"] = True
        else:
            self.active_violations["bent_knees"] = False
            
        # Accumulate violations if we are inside a rep
        if self.state != "UP":
            for k, v in self.active_violations.items():
                if v:
                    self.current_rep_violations[k] = True
                    
        # State Machine Transition logic
        rep_completed = False
        rep_status = None
        
        if self.state == "UP":
            # Start descent
            if elbow_angle < up_threshold - 5.0:
                self.state = "DESCENT"
                self.min_elbow_angle = elbow_angle
                self.current_rep_violations = {
                    "hip_sagging": False,
                    "hip_piking": False,
                    "bent_knees": False
                }
        elif self.state == "DESCENT":
            self.min_elbow_angle = min(self.min_elbow_angle, elbow_angle)
            
            # If the user starts rising again (angle increases by 8 degrees)
            if elbow_angle > self.min_elbow_angle + 8.0:
                if self.min_elbow_angle < 125.0:
                    self.state = "ASCENT"
                else:
                    # Too shallow to count, return to UP
                    self.state = "UP"
            elif elbow_angle > up_threshold:
                self.state = "UP"
                
        elif self.state == "ASCENT":
            # Track any deeper extension during ascent (pause at bottom)
            if elbow_angle < self.min_elbow_angle:
                self.min_elbow_angle = elbow_angle
                
            # Completed rep (returned to top position)
            if elbow_angle > up_threshold - 3.0:
                self.rep_count += 1
                rep_completed = True
                
                # Determine quality based on minimum elbow angle achieved
                if self.min_elbow_angle <= 95.0:
                    rep_status = "GOOD"
                    self.good_reps += 1
                elif self.min_elbow_angle <= 115.0:
                    rep_status = "SHALLOW"
                    self.shallow_reps += 1
                else:
                    rep_status = "INVALID"
                    
                # Save rep info
                rep_info = {
                    "rep_index": self.rep_count,
                    "min_elbow_angle": round(self.min_elbow_angle, 1),
                    "status": rep_status,
                    "violations": {k: v for k, v in self.current_rep_violations.items()}
                }
                self.reps_history.append(rep_info)
                self.state = "UP"
                
        return rep_completed, rep_status

def calculate_angle_3d(p1, p2, p3):
    """Calculates angle at p2 between vectors p1-p2 and p3-p2 in 3D space."""
    u = np.array([p1.x, p1.y, p1.z]) - np.array([p2.x, p2.y, p2.z])
    v = np.array([p3.x, p3.y, p3.z]) - np.array([p2.x, p2.y, p2.z])
    dot_product = np.dot(u, v)
    norm_u = np.linalg.norm(u)
    norm_v = np.linalg.norm(v)
    if norm_u == 0 or norm_v == 0:
        return 0.0
    cos_theta = dot_product / (norm_u * norm_v)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_theta)))

def get_landmark_visibility(landmarks, indices):
    """Returns the average visibility score of specified landmarks."""
    visibilities = [landmarks[i].visibility for i in indices if i < len(landmarks)]
    return np.mean(visibilities) if visibilities else 0.0

def draw_styled_text(img, text, position, font_scale=0.6, color=(255, 255, 255), thickness=1):
    """Draws a clean text label with a black shadow outline for readability on any background."""
    x, y = position
    # Draw outline/shadow
    cv2.putText(img, text, (x + 1, y + 1), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
    # Draw main text
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)

def analyze_pushup_video(input_video_path, output_video_path, json_output_path):
    # Ensure directory existence
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)

    # 1. Open Video
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {input_video_path}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0:
        fps = 30.0

    print(f"Loaded video: {os.path.basename(input_video_path)}")
    print(f"Properties: {width}x{height} | {fps:.1f} FPS | {total_frames} frames")

    # 2. Setup Video Writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # 3. Setup MediaPipe Landmarker
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model file not found at {MODEL_PATH}")
        return

    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO
    )

    tracker = PushupStateTracker()
    frame_metrics = []

    print("Running biomechanical analysis...")
    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        frame_idx = 0
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            timestamp_ms = int((frame_idx / fps) * 1000)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Detect pose
            result = landmarker.detect_for_video(mp_image, timestamp_ms)
            annotated_frame = frame.copy()

            if result.pose_landmarks and len(result.pose_landmarks) > 0:
                landmarks = result.pose_landmarks[0]
                world_landmarks = result.pose_world_landmarks[0]

                # Determine the most visible side of the user's body
                left_indices = [11, 13, 15, 23, 25, 27]  # Shoulder, Elbow, Wrist, Hip, Knee, Ankle
                right_indices = [12, 14, 16, 24, 26, 28]
                left_vis = get_landmark_visibility(landmarks, left_indices)
                right_vis = get_landmark_visibility(landmarks, right_indices)

                side_label = "Left" if left_vis >= right_vis else "Right"
                
                # Assign landmarks based on the dominant side
                if side_label == "Left":
                    sh_idx, el_idx, wr_idx = 11, 13, 15
                    hip_idx, kn_idx, ak_idx = 23, 25, 27
                else:
                    sh_idx, el_idx, wr_idx = 12, 14, 16
                    hip_idx, kn_idx, ak_idx = 24, 26, 28

                # Verify joint visibility
                sh_lm, el_lm, wr_lm = world_landmarks[sh_idx], world_landmarks[el_idx], world_landmarks[wr_idx]
                hip_lm, kn_lm, ak_lm = world_landmarks[hip_idx], world_landmarks[kn_idx], world_landmarks[ak_idx]
                
                sh_vis = landmarks[sh_idx].visibility
                el_vis = landmarks[el_idx].visibility
                wr_vis = landmarks[wr_idx].visibility
                hip_vis = landmarks[hip_idx].visibility
                kn_vis = landmarks[kn_idx].visibility
                ak_vis = landmarks[ak_idx].visibility

                # Compute angles if visibility threshold is met
                min_vis = 0.5
                if sh_vis > min_vis and el_vis > min_vis and wr_vis > min_vis:
                    elbow_angle = calculate_angle_3d(sh_lm, el_lm, wr_lm)
                else:
                    elbow_angle = 180.0 # Default straight

                if sh_vis > min_vis and hip_vis > min_vis and ak_vis > min_vis:
                    hip_angle = calculate_angle_3d(sh_lm, hip_lm, ak_lm)
                else:
                    hip_angle = 180.0

                if hip_vis > min_vis and kn_vis > min_vis and ak_vis > min_vis:
                    knee_angle = calculate_angle_3d(hip_lm, kn_lm, ak_lm)
                else:
                    knee_angle = 180.0

                # Update State Tracker
                rep_completed, rep_status = tracker.update(elbow_angle, hip_angle, knee_angle)

                # Record metrics for JSON dump
                frame_metrics.append({
                    "frame": frame_idx,
                    "timestamp_ms": timestamp_ms,
                    "active_side": side_label,
                    "elbow_angle": round(elbow_angle, 2),
                    "hip_angle": round(hip_angle, 2),
                    "knee_angle": round(knee_angle, 2),
                    "state": tracker.state,
                    "active_violations": {k: v for k, v in tracker.active_violations.items()}
                })

                # ---- VISUAL FEEDBACK (HUD & SKELETON) ----
                # Pixel coordinate points for drawing
                pixel_points = {}
                for idx in [sh_idx, el_idx, wr_idx, hip_idx, kn_idx, ak_idx]:
                    lm = landmarks[idx]
                    cx, cy = int(lm.x * width), int(lm.y * height)
                    pixel_points[idx] = (cx, cy)

                # Determine joint connection colors based on form violations
                # Hip Sagging or Piking colors the spine red. Otherwise Cyan.
                spine_color = (60, 60, 255) if (tracker.active_violations["hip_sagging"] or tracker.active_violations["hip_piking"]) else (255, 191, 0)
                # Knee bending colors the thigh/shin red. Otherwise Cyan.
                knee_color = (60, 60, 255) if tracker.active_violations["bent_knees"] else (255, 191, 0)
                
                # Range of motion warning (yellow elbows if shallow)
                elbow_color = (255, 191, 0)
                if tracker.state != "UP":
                    if tracker.min_elbow_angle > 115.0:
                        elbow_color = (60, 60, 255)  # Red for way too shallow
                    elif tracker.min_elbow_angle > 95.0:
                        elbow_color = (0, 215, 255)  # Orange/yellow for slightly shallow

                # Draw skeleton lines
                if sh_idx in pixel_points and el_idx in pixel_points:
                    cv2.line(annotated_frame, pixel_points[sh_idx], pixel_points[el_idx], elbow_color, 4, cv2.LINE_AA)
                if el_idx in pixel_points and wr_idx in pixel_points:
                    cv2.line(annotated_frame, pixel_points[el_idx], pixel_points[wr_idx], elbow_color, 4, cv2.LINE_AA)
                if sh_idx in pixel_points and hip_idx in pixel_points:
                    cv2.line(annotated_frame, pixel_points[sh_idx], pixel_points[hip_idx], spine_color, 4, cv2.LINE_AA)
                if hip_idx in pixel_points and kn_idx in pixel_points:
                    cv2.line(annotated_frame, pixel_points[hip_idx], pixel_points[kn_idx], knee_color, 4, cv2.LINE_AA)
                if kn_idx in pixel_points and ak_idx in pixel_points:
                    cv2.line(annotated_frame, pixel_points[kn_idx], pixel_points[ak_idx], knee_color, 4, cv2.LINE_AA)

                # Draw connection circles
                for idx, point in pixel_points.items():
                    cv2.circle(annotated_frame, point, 8, (255, 255, 255), -1, cv2.LINE_AA)
                    cv2.circle(annotated_frame, point, 5, (0, 0, 255) if idx in [el_idx, hip_idx] else (0, 255, 0), -1, cv2.LINE_AA)

                # ---- HUD DASHBOARD (Glassmorphic) ----
                # Draw semi-transparent rectangle for background
                hud_overlay = annotated_frame.copy()
                # Left Panel
                cv2.rectangle(hud_overlay, (20, 20), (360, 200), (30, 30, 30), -1)
                # Right Panel (Warnings)
                cv2.rectangle(hud_overlay, (width - 340, 20), (width - 20, 200), (30, 30, 30), -1)
                
                # Apply blending
                cv2.addWeighted(hud_overlay, 0.7, annotated_frame, 0.3, 0, annotated_frame)

                # Write Left HUD values
                draw_styled_text(annotated_frame, "CALIS APP | BIOMECHANICS ENGINE", (30, 45), font_scale=0.5, color=(0, 255, 255), thickness=2)
                draw_styled_text(annotated_frame, f"REPS: {tracker.rep_count}", (30, 80), font_scale=0.8, color=(255, 255, 255), thickness=2)
                draw_styled_text(annotated_frame, f"GOOD: {tracker.good_reps}   SHALLOW: {tracker.shallow_reps}", (30, 110), font_scale=0.5, color=(100, 255, 100), thickness=1)
                draw_styled_text(annotated_frame, f"PHASE: {tracker.state}", (30, 140), font_scale=0.6, color=(255, 150, 0), thickness=2)
                draw_styled_text(annotated_frame, f"ANALYZED SIDE: {side_label.upper()}", (30, 165), font_scale=0.45, color=(200, 200, 200), thickness=1)
                draw_styled_text(annotated_frame, f"ELBOW: {elbow_angle:.1f}*   HIP: {hip_angle:.1f}*", (30, 185), font_scale=0.45, color=(200, 200, 200), thickness=1)

                # Write Right HUD (Warnings & Live feedback)
                draw_styled_text(annotated_frame, "LIVE FORM CHECKS", (width - 320, 45), font_scale=0.5, color=(0, 215, 255), thickness=2)
                
                warn_y = 80
                active_warns = []
                if tracker.active_violations["hip_sagging"]:
                    draw_styled_text(annotated_frame, "WARNING: HIP SAGGING", (width - 320, warn_y), font_scale=0.5, color=(60, 60, 255), thickness=2)
                    warn_y += 30
                    active_warns.append("hip_sagging")
                if tracker.active_violations["hip_piking"]:
                    draw_styled_text(annotated_frame, "WARNING: HIP PIKING", (width - 320, warn_y), font_scale=0.5, color=(60, 60, 255), thickness=2)
                    warn_y += 30
                    active_warns.append("hip_piking")
                if tracker.active_violations["bent_knees"]:
                    draw_styled_text(annotated_frame, "WARNING: BENT KNEES", (width - 320, warn_y), font_scale=0.5, color=(0, 200, 255), thickness=2)
                    warn_y += 30
                    active_warns.append("bent_knees")

                if tracker.state != "UP" and tracker.min_elbow_angle > 95.0:
                    depth_status = "SHALLOW" if tracker.min_elbow_angle <= 115.0 else "TOO SHALLOW"
                    draw_styled_text(annotated_frame, f"DEPTH: {depth_status}", (width - 320, warn_y), font_scale=0.5, color=(0, 165, 255) if depth_status == "SHALLOW" else (60, 60, 255), thickness=2)
                    warn_y += 30
                    active_warns.append("shallow_depth")

                if not active_warns:
                    draw_styled_text(annotated_frame, "FORM ALIGNMENT: GOOD", (width - 320, 90), font_scale=0.6, color=(50, 255, 50), thickness=2)

                # ---- DEPTH GAUGE (Right hand progress bar) ----
                # Vertical gauge showing how low the user goes (based on elbow angle between 180° and 90°)
                gauge_x = width - 50
                gauge_y_start = 240
                gauge_y_end = height - 100
                gauge_height = gauge_y_end - gauge_y_start
                
                # Draw outline
                cv2.rectangle(annotated_frame, (gauge_x, gauge_y_start), (gauge_x + 15, gauge_y_end), (255, 255, 255), 2, cv2.LINE_AA)
                
                # Fill bar based on flexion (180° => 0% fill, 90° => 100% fill)
                flexion_pct = np.clip((180.0 - elbow_angle) / 90.0, 0.0, 1.0)
                fill_height = int(flexion_pct * gauge_height)
                
                # Draw green bar up to fill height
                bar_color = (0, 255, 0) if elbow_angle <= 95.0 else (0, 215, 255) if elbow_angle <= 115.0 else (0, 0, 255)
                cv2.rectangle(annotated_frame, (gauge_x + 2, gauge_y_end - fill_height), (gauge_x + 13, gauge_y_end - 2), bar_color, -1)
                
                # Draw target line at 90° (which is 100% target depth)
                target_y = gauge_y_end - int(1.0 * gauge_height)
                cv2.line(annotated_frame, (gauge_x - 5, target_y), (gauge_x + 20, target_y), (0, 255, 255), 2)
                draw_styled_text(annotated_frame, "TARGET DEPTH", (gauge_x - 130, target_y + 5), font_scale=0.35, color=(0, 255, 255), thickness=1)

                # Flash success text on completed rep
                if rep_completed:
                    text_flash = f"REP {tracker.rep_count} {rep_status}!"
                    flash_color = (0, 255, 0) if rep_status == "GOOD" else (0, 180, 255)
                    # Overlay bold centered text
                    cv2.putText(annotated_frame, text_flash, (width // 2 - 150, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 6, cv2.LINE_AA)
                    cv2.putText(annotated_frame, text_flash, (width // 2 - 150, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, flash_color, 3, cv2.LINE_AA)

            else:
                # No person detected
                cv2.putText(annotated_frame, "NO PERSON DETECTED", (width // 2 - 200, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3, cv2.LINE_AA)

            # Write output
            out.write(annotated_frame)
            frame_idx += 1
            if total_frames > 0:
                print(f"\rProgress: {frame_idx}/{total_frames} frames ({int((frame_idx/total_frames)*100)}%)", end="")
            else:
                print(f"\rProgress: {frame_idx} frames processed", end="")

    print("\nProcessing complete! Finalizing output files...")
    cap.release()
    out.release()

    # Generate JSON summary
    summary_report = {
        "video_analysis_summary": {
            "input_file": os.path.basename(input_video_path),
            "total_frames": frame_idx,
            "total_reps": tracker.rep_count,
            "good_reps": tracker.good_reps,
            "shallow_reps": tracker.shallow_reps,
            "invalid_reps": tracker.rep_count - (tracker.good_reps + tracker.shallow_reps)
        },
        "reps_detail": tracker.reps_history,
        "frame_by_frame_metrics": frame_metrics
    }

    with open(json_output_path, "w") as f:
        json.dump(summary_report, f, indent=4)
        
    print(f"Annotated video saved to: {output_video_path}")
    print(f"JSON metrics saved to: {json_output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MediaPipe Pushup Biomechanics Heuristics Analyzer")
    parser.add_argument("--input", type=str, default=os.path.join(INPUT_DIR, "correct-wrong.mp4"),
                        help="Path to input pushup video")
    parser.add_argument("--output", type=str, default=os.path.join(OUTPUT_DIR, "correct-wrong_pushup_analysis.mp4"),
                        help="Path to output annotated video")
    parser.add_argument("--json", type=str, default=os.path.join(OUTPUT_DIR, "correct-wrong_pushup_report.json"),
                        help="Path to output JSON analysis results")
    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}")
        print(f"Please specify a valid input path or copy 'correct-wrong.mp4' into {INPUT_DIR}")
        sys.exit(1)

    analyze_pushup_video(args.input, args.output, args.json)
