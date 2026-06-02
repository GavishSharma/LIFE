import cv2
import math
import time

# --- Config ---
SHOW_ORIENTATION = True   # Set to False to hide angle arrow and angle text
CAMERA_INDEX     = 0      # Change if using a different camera
FRAME_WIDTH      = 640
FRAME_HEIGHT     = 480
ARUCO_DICT       = cv2.aruco.DICT_4X4_250
PRINT_INTERVAL   = 0.25   # seconds between console prints (camera stays smooth)


def setup_detector():
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    parameters = cv2.aruco.DetectorParameters()
    detector   = cv2.aruco.ArucoDetector(dictionary, parameters)
    return detector


def get_angle(corners):
    """Return the forward-facing angle (0–360°) from the marker's top-edge direction."""
    c0, c1, c2, c3 = corners   # TL, TR, BR, BL

    cx = (c0[0] + c1[0] + c2[0] + c3[0]) / 4
    cy = (c0[1] + c1[1] + c2[1] + c3[1]) / 4

    # Midpoint of the top edge = "front" of the marker
    tx = (c0[0] + c1[0]) / 2
    ty = (c0[1] + c1[1]) / 2

    # Invert Y because OpenCV's Y-axis points downward
    angle = math.degrees(math.atan2(-(ty - cy), tx - cx)) % 360
    return int(angle), (int(cx), int(cy)), (int(tx), int(ty))


def draw_marker_info(frame, marker_corners, marker_id):
    """Draw overlay on the frame. Returns a summary string for console printing."""
    top_left = (int(marker_corners[0][0]), int(marker_corners[0][1]))

    if SHOW_ORIENTATION:
        angle, center, tip = get_angle(marker_corners)
        cv2.arrowedLine(frame, center, tip, (0, 0, 255), 3, tipLength=0.3)  # red arrow
        cv2.circle(frame, center, 5, (255, 0, 0), -1)                       # blue dot
        label = f"ID: {marker_id} | {angle}deg"
        summary = f"  ID {marker_id:>3} | {angle:>3}°"
    else:
        label = f"ID: {marker_id}"
        summary = f"  ID {marker_id:>3}"

    cv2.putText(frame, label,
                (top_left[0], top_left[1] - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (0, 255, 0), 2, cv2.LINE_AA)

    return summary


def print_detections(summaries):
    """Print all detected markers in one clean console block."""
    print(f"[{time.strftime('%H:%M:%S')}] {len(summaries)} marker(s) detected:")
    for s in summaries:
        print(s)
    print()


def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Could not open camera. Check the connection or CAMERA_INDEX.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    detector = setup_detector()
    last_print_time = 0.0

    print("Detection started — press 'q' to quit.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        corners, ids, _ = detector.detectMarkers(frame)

        summaries = []
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

            for i, marker_id in enumerate(ids.flatten()):
                summary = draw_marker_info(frame, corners[i][0], marker_id)
                summaries.append(summary)

        # Print to console at most every PRINT_INTERVAL seconds
        now = time.monotonic()
        if summaries and (now - last_print_time) >= PRINT_INTERVAL:
            print_detections(summaries)
            last_print_time = now

        cv2.imshow("ArUco Detector", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Done.")


if __name__ == "__main__":
    main()
