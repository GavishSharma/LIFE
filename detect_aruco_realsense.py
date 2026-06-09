import cv2
import math
import time
import numpy as np
import pyrealsense2 as rs

# --- Config ---
SHOW_ORIENTATION = True
FRAME_WIDTH      = 640
FRAME_HEIGHT     = 480
ARUCO_DICT       = cv2.aruco.DICT_4X4_250
PRINT_INTERVAL   = 0.25


def setup_detector():
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)
    return detector


def get_angle(corners):
    c0, c1, c2, c3 = corners

    cx = (c0[0] + c1[0] + c2[0] + c3[0]) / 4
    cy = (c0[1] + c1[1] + c2[1] + c3[1]) / 4

    tx = (c0[0] + c1[0]) / 2
    ty = (c0[1] + c1[1]) / 2

    angle = math.degrees(math.atan2(-(ty - cy), tx - cx)) % 360
    return int(angle), (int(cx), int(cy)), (int(tx), int(ty))


def draw_marker_info(frame, marker_corners, marker_id):
    top_left = (int(marker_corners[0][0]), int(marker_corners[0][1]))

    if SHOW_ORIENTATION:
        angle, center, tip = get_angle(marker_corners)
        cv2.arrowedLine(frame, center, tip, (0, 0, 255), 3, tipLength=0.3)
        cv2.circle(frame, center, 5, (255, 0, 0), -1)
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
    print(f"[{time.strftime('%H:%M:%S')}] {len(summaries)} marker(s) detected:")
    for s in summaries:
        print(s)
    print()


def main():

    # -----------------------------
    # RealSense setup
    # -----------------------------
    pipeline = rs.pipeline()
    config = rs.config()

    config.enable_stream(rs.stream.color,
                         FRAME_WIDTH,
                         FRAME_HEIGHT,
                         rs.format.bgr8,
                         30)

    pipeline.start(config)

    print("RealSense camera started.")

    detector = setup_detector()
    last_print_time = 0.0

    try:
        while True:

            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue

            frame = np.asanyarray(color_frame.get_data())

            corners, ids, _ = detector.detectMarkers(frame)

            summaries = []

            if ids is not None:
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)

                for i, marker_id in enumerate(ids.flatten()):
                    summary = draw_marker_info(frame, corners[i][0], marker_id)
                    summaries.append(summary)

            # console print throttled
            now = time.monotonic()
            if summaries and (now - last_print_time) >= PRINT_INTERVAL:
                print_detections(summaries)
                last_print_time = now

            cv2.imshow("ArUco + RealSense D435", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()
        print("Stopped cleanly.")


if __name__ == "__main__":
    main()