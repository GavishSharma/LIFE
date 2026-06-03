import cv2
import math
import time

# --- Config ---#
SHOW_ORIENTATION    = True    # Show angle arrow and degrees
CAMERA_INDEX        = 0
FRAME_WIDTH         = 640
FRAME_HEIGHT        = 480
PRINT_INTERVAL      = 0.25   # seconds between console prints

# --- Dictionary: try these if detection fails ---
# DICT_4X4_50, DICT_4X4_100, DICT_5X5_50, DICT_6X6_50, DICT_ARUCO_ORIGINAL
ARUCO_DICT          = cv2.aruco.DICT_4X4_50

# --- Distance Config ---
MARKER_REAL_SIZE_CM = 5.0    # Physical printed size of your marker in cm
FOCAL_LENGTH_PX     = None   # None = auto-calibrate; or hardcode e.g. 800.0

# --- Debug ---
DEBUG = True   # Shows grayscale + rejected candidates window to diagnose detection


# ─────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────

def setup_detector():
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    params     = cv2.aruco.DetectorParameters()

    # More lenient detection — helps with printed/phone-screen markers
    params.adaptiveThreshWinSizeMin  = 3
    params.adaptiveThreshWinSizeMax  = 53
    params.adaptiveThreshWinSizeStep = 4
    params.minMarkerPerimeterRate    = 0.02   # detect smaller markers
    params.maxMarkerPerimeterRate    = 4.0
    params.polygonalApproxAccuracyRate = 0.05
    params.cornerRefinementMethod    = cv2.aruco.CORNER_REFINE_SUBPIX

    return cv2.aruco.ArucoDetector(dictionary, params)


# ─────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────

def get_marker_size_px(corners):
    c0, c1, c2, c3 = corners
    sides = [
        math.dist(c0, c1),
        math.dist(c1, c2),
        math.dist(c2, c3),
        math.dist(c3, c0),
    ]
    return sum(sides) / 4


def get_center(corners):
    cx = sum(c[0] for c in corners) / 4
    cy = sum(c[1] for c in corners) / 4
    return (cx, cy)


def get_angle(corners):
    c0, c1, c2, c3 = corners
    cx, cy = get_center(corners)
    tx = (c0[0] + c1[0]) / 2
    ty = (c0[1] + c1[1]) / 2
    angle = math.degrees(math.atan2(-(ty - cy), tx - cx)) % 360
    return int(angle), (int(cx), int(cy)), (int(tx), int(ty))


def estimate_focal_length(marker_size_px):
    CALIBRATION_DISTANCE_CM = 20.0
    return (marker_size_px * CALIBRATION_DISTANCE_CM) / MARKER_REAL_SIZE_CM


def estimate_depth_cm(marker_size_px, focal_length):
    return (MARKER_REAL_SIZE_CM * focal_length) / marker_size_px


def calculate_distance_cm(corners_a, corners_b, focal_length):
    size_a  = get_marker_size_px(corners_a)
    size_b  = get_marker_size_px(corners_b)
    depth_a = estimate_depth_cm(size_a, focal_length)
    depth_b = estimate_depth_cm(size_b, focal_length)
    avg_depth = (depth_a + depth_b) / 2

    px_per_cm = focal_length / avg_depth
    dx_cm = (get_center(corners_b)[0] - get_center(corners_a)[0]) / px_per_cm
    dy_cm = (get_center(corners_b)[1] - get_center(corners_a)[1]) / px_per_cm
    dz_cm = depth_b - depth_a

    distance = math.sqrt(dx_cm**2 + dy_cm**2 + dz_cm**2)
    return round(distance, 1), round(depth_a, 1), round(depth_b, 1)


# ─────────────────────────────────────────────
# Drawing
# ─────────────────────────────────────────────

def draw_marker_info(frame, marker_corners, marker_id):
    top_left = (int(marker_corners[0][0]), int(marker_corners[0][1]))

    if SHOW_ORIENTATION:
        angle, center, tip = get_angle(marker_corners)
        cv2.arrowedLine(frame, center, tip, (0, 0, 255), 3, tipLength=0.3)
        cv2.circle(frame, center, 5, (255, 0, 0), -1)
        label   = f"ID: {marker_id} | {angle}deg"
        summary = f"  ID {marker_id:>3} | {angle:>3}°"
    else:
        label   = f"ID: {marker_id}"
        summary = f"  ID {marker_id:>3}"

    cv2.putText(frame, label,
                (top_left[0], top_left[1] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (0, 255, 0), 2, cv2.LINE_AA)
    return summary


def draw_distance(frame, corners_a, corners_b, distance_cm):
    ca  = tuple(int(v) for v in get_center(corners_a))
    cb  = tuple(int(v) for v in get_center(corners_b))
    mid = ((ca[0] + cb[0]) // 2, (ca[1] + cb[1]) // 2)
    cv2.line(frame, ca, cb, (255, 255, 0), 2)
    cv2.putText(frame, f"{distance_cm} cm",
                (mid[0] + 5, mid[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 0), 2, cv2.LINE_AA)


def draw_debug(frame, rejected):
    """
    Shows a second window with:
    - Grayscale + adaptive threshold (what the detector actually sees)
    - Yellow boxes around rejected candidates (squares it saw but couldn't decode)
    """
    gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    thresh  = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        21, 7
    )
    debug   = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    # Draw rejected squares in yellow so you can see what the detector tried
    if rejected:
        for r in rejected:
            pts = r[0].astype(int)
            cv2.polylines(debug, [pts], True, (0, 255, 255), 1)

    count = len(rejected) if rejected else 0
    cv2.putText(debug, f"Rejected: {count}",
                (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (0, 180, 255), 1, cv2.LINE_AA)

    cv2.imshow("Debug — Threshold View", debug)


# ─────────────────────────────────────────────
# Console output
# ─────────────────────────────────────────────

def print_detections(summaries, distance_info=None):
    print(f"[{time.strftime('%H:%M:%S')}] {len(summaries)} marker(s) detected:")
    for s in summaries:
        print(s)
    if distance_info:
        dist, d0, d1 = distance_info
        print(f"  Distance between markers : {dist} cm")
        print(f"  Depth — marker 0: {d0} cm | marker 1: {d1} cm")
    print()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    global FOCAL_LENGTH_PX

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Could not open camera. Check CAMERA_INDEX.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    detector        = setup_detector()
    last_print_time = 0.0
    calibrated      = FOCAL_LENGTH_PX is not None

    print("Detection started — press 'q' to quit.")
    if DEBUG:
        print("DEBUG mode ON — check the 'Debug — Threshold View' window.")
        print("  If you see yellow boxes: marker shape found but not decoded")
        print("    → likely wrong dictionary, too blurry, or too much glare")
        print("  If NO yellow boxes: marker not even found as a square")
        print("    → too dark, bad contrast, or marker too small/far\n")
    if not calibrated:
        print(f"Auto-calibration: hold a marker exactly 20 cm from camera on first detection.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        frame = cv2.flip(frame, 1)

        corners, ids, rejected = detector.detectMarkers(frame)

        summaries     = []
        distance_info = None

        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

            if not calibrated:
                FOCAL_LENGTH_PX = estimate_focal_length(get_marker_size_px(corners[0][0]))
                calibrated = True
                print(f"[Calibrated] Focal length = {FOCAL_LENGTH_PX:.1f} px\n")

            for i, marker_id in enumerate(ids.flatten()):
                summaries.append(draw_marker_info(frame, corners[i][0], marker_id))

            if len(ids) == 2:
                dist, d0, d1 = calculate_distance_cm(
                    corners[0][0], corners[1][0], FOCAL_LENGTH_PX
                )
                draw_distance(frame, corners[0][0], corners[1][0], dist)
                distance_info = (dist, d0, d1)

        if DEBUG:
            draw_debug(frame, rejected)

        now = time.monotonic()
        if summaries and (now - last_print_time) >= PRINT_INTERVAL:
            print_detections(summaries, distance_info)
            last_print_time = now

        cv2.imshow("ArUco Detector", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Done.")


if __name__ == "__main__":
    main()
