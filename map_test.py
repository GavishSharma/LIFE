"""
ArUco Tracker — LIFE Project
Corner markers: ID 0 (bottom-left), 1 (bottom-right), 10 (top-left), 11 (top-right)
Real-world square: 1m x 1m, marker size: 8cm x 8cm
Dict: DICT_4X4_80
"""

import cv2
import numpy as np

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
DICT_TYPE        = cv2.aruco.DICT_4X4_250
MARKER_SIZE_M    = 0.08          # 8 cm
SQUARE_SIZE_M    = 1.0           # 1 m
OUTPUT_WIN_PX    = 800           # output window size in pixels
CORNER_IDS       = {0, 1, 10, 11}
CAMERA_INDEX     = 0

# Real-world coords (meters) of the CENTRE of each corner marker
# Origin = ID 0 centre, x→right, y→up
HALF = MARKER_SIZE_M / 2
CORNER_WORLD = {
    0:  np.array([0.0 + HALF,              0.0 + HALF],              dtype=np.float32),
    1:  np.array([SQUARE_SIZE_M - HALF,    0.0 + HALF],              dtype=np.float32),
    10: np.array([0.0 + HALF,              SQUARE_SIZE_M - HALF],    dtype=np.float32),
    11: np.array([SQUARE_SIZE_M - HALF,    SQUARE_SIZE_M - HALF],    dtype=np.float32),
}

# ──────────────────────────────────────────────
# APPROX CALIBRATION from 4 coplanar markers
# ──────────────────────────────────────────────
def calibrate_from_corners(image_points_dict, frame_shape):
    """
    One-shot approximate calibration using the 4 known corner markers.
    image_points_dict: {id: corner_array (4,2)} from ArUco detection
    Returns: camera_matrix, dist_coeffs  (None, None if not enough data)
    """
    obj_pts_all = []
    img_pts_all = []

    for mid, img_corners in image_points_dict.items():
        if mid not in CORNER_WORLD:
            continue
        cx, cy = CORNER_WORLD[mid]
        half = MARKER_SIZE_M / 2
        # 4 corners of marker in 3-D (Z=0 flat ground)
        obj = np.array([
            [cx - half, cy - half, 0],
            [cx + half, cy - half, 0],
            [cx + half, cy + half, 0],
            [cx - half, cy + half, 0],
        ], dtype=np.float32)
        obj_pts_all.append(obj)
        img_pts_all.append(img_corners.astype(np.float32))

    if len(obj_pts_all) < 4:
        return None, None

    h, w = frame_shape[:2]
    # Naive initial guess for camera matrix
    focal = max(h, w)
    cam_init = np.array([[focal, 0, w/2],
                         [0, focal, h/2],
                         [0,     0,   1]], dtype=np.float64)
    dist_init = np.zeros(5)

    flags = (cv2.CALIB_USE_INTRINSIC_GUESS |
             cv2.CALIB_FIX_ASPECT_RATIO   |
             cv2.CALIB_ZERO_TANGENT_DIST  )

    ret, cam_mat, dist, _, _ = cv2.calibrateCamera(
        obj_pts_all, img_pts_all, (w, h),
        cam_init, dist_init, flags=flags
    )
    if ret:
        print(f"[CALIB] RMS reprojection error: {ret:.4f} px")
        return cam_mat, dist
    return None, None


# ──────────────────────────────────────────────
# HOMOGRAPHY  (image → top-down pixel space)
# ──────────────────────────────────────────────
def compute_homography(image_points_dict):
    """
    image_points_dict: {id: (4,2) corner array}
    Returns 3x3 homography H  (None if <4 corners detected)
    """
    src = []   # image pixel coords of marker centres
    dst = []   # output window pixel coords

    scale = OUTPUT_WIN_PX / SQUARE_SIZE_M   # px per metre

    for mid, img_corners in image_points_dict.items():
        if mid not in CORNER_WORLD:
            continue
        # marker centre in image
        cx_img = img_corners[:, 0].mean()
        cy_img = img_corners[:, 1].mean()
        src.append([cx_img, cy_img])

        # marker centre in output window (flip y: image y↓, world y↑)
        wx, wy = CORNER_WORLD[mid]
        px = wx * scale
        py = (SQUARE_SIZE_M - wy) * scale   # flip y
        dst.append([px, py])

    if len(src) < 4:
        return None

    src = np.array(src, dtype=np.float32)
    dst = np.array(dst, dtype=np.float32)
    H, _ = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    return H


# ──────────────────────────────────────────────
# WARP a single point through H
# ──────────────────────────────────────────────
def warp_point(H, px, py):
    pt = np.array([[[px, py]]], dtype=np.float32)
    warped = cv2.perspectiveTransform(pt, H)
    return int(warped[0, 0, 0]), int(warped[0, 0, 1])


# ──────────────────────────────────────────────
# DRAW top-down map
# ──────────────────────────────────────────────
TRAIL_COLORS = [
    (0, 200, 255), (0, 255, 100), (255, 100, 0),
    (200, 0, 255), (255, 220, 0), (0, 180, 180),
]

def draw_map(tracked, trails):
    canvas = np.zeros((OUTPUT_WIN_PX, OUTPUT_WIN_PX, 3), dtype=np.uint8)

    # Border
    cv2.rectangle(canvas, (2, 2), (OUTPUT_WIN_PX-3, OUTPUT_WIN_PX-3), (80, 80, 80), 2)

    # Grid lines (every 0.25 m)
    step = int(OUTPUT_WIN_PX * 0.25)
    for i in range(1, 4):
        v = i * step
        cv2.line(canvas, (v, 0), (v, OUTPUT_WIN_PX), (30, 30, 30), 1)
        cv2.line(canvas, (0, v), (OUTPUT_WIN_PX, v), (30, 30, 30), 1)

    # Corner labels
    margin = 12
    cv2.putText(canvas, "ID0", (margin, OUTPUT_WIN_PX - margin),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)
    cv2.putText(canvas, "ID1", (OUTPUT_WIN_PX - 40, OUTPUT_WIN_PX - margin),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)
    cv2.putText(canvas, "ID10", (margin, margin + 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)
    cv2.putText(canvas, "ID11", (OUTPUT_WIN_PX - 45, margin + 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)

    # Trails + markers
    for idx, (mid, (mx, my)) in enumerate(tracked.items()):
        color = TRAIL_COLORS[idx % len(TRAIL_COLORS)]

        # draw trail
        trail = trails.get(mid, [])
        for i in range(1, len(trail)):
            cv2.line(canvas, trail[i-1], trail[i], color, 1)

        # current position dot
        cv2.circle(canvas, (mx, my), 7, color, -1)
        cv2.putText(canvas, f"ID{mid}", (mx + 9, my - 9),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    return canvas


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera.")
        return

    aruco_dict   = cv2.aruco.getPredefinedDictionary(DICT_TYPE)
    aruco_params = cv2.aruco.DetectorParameters()

    # Tighten params to reduce false positives
    aruco_params.adaptiveThreshWinSizeMin  = 3
    aruco_params.adaptiveThreshWinSizeMax  = 23
    aruco_params.adaptiveThreshWinSizeStep = 4
    aruco_params.minMarkerPerimeterRate    = 0.03
    aruco_params.maxMarkerPerimeterRate    = 0.5
    aruco_params.polygonalApproxAccuracyRate = 0.05
    aruco_params.minCornerDistanceRate     = 0.05
    aruco_params.errorCorrectionRate       = 0.6

    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

    cam_matrix  = None
    dist_coeffs = None
    H           = None
    calibrated  = False

    # {marker_id: [(px,py), ...]}
    trails  = {}
    # {marker_id: (px, py)}  current position on map
    tracked = {}

    MAX_TRAIL = 300   # points per trail

    print("[INFO] Press 'r' to reset homography | 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Frame read failed.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # CLAHE for low-contrast improvement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray  = clahe.apply(gray)

        corners_list, ids, _ = detector.detectMarkers(gray)

        display = frame.copy()
        image_pts_dict = {}   # {id: (4,2) array}

        if ids is not None:
            cv2.aruco.drawDetectedMarkers(display, corners_list, ids)
            for i, mid in enumerate(ids.flatten()):
                c = corners_list[i][0]   # shape (4,2)
                image_pts_dict[mid] = c

            # ── Calibration (once, when all 4 corners visible) ──
            if not calibrated:
                corner_pts = {k: v for k, v in image_pts_dict.items() if k in CORNER_IDS}
                if len(corner_pts) == 4:
                    cam_matrix, dist_coeffs = calibrate_from_corners(corner_pts, frame.shape)
                    if cam_matrix is not None:
                        calibrated = True
                        print("[CALIB] Done.")

            # ── Undistort corners for homography (if calibrated) ──
            if calibrated and cam_matrix is not None:
                undist_dict = {}
                for mid, c in image_pts_dict.items():
                    pts = cv2.undistortPoints(
                        c.reshape(1, 4, 2), cam_matrix, dist_coeffs,
                        P=cam_matrix
                    ).reshape(4, 2)
                    undist_dict[mid] = pts
            else:
                undist_dict = image_pts_dict

            # ── Homography ──
            corner_present = CORNER_IDS.issubset(set(undist_dict.keys()))
            if H is None and corner_present:
                H = compute_homography(undist_dict)
                if H is not None:
                    print("[HOMO] Computed.")
            elif H is not None and corner_present:
                # Recompute if corners moved (shouldn't happen, but safety)
                H_new = compute_homography(undist_dict)
                if H_new is not None:
                    H = H_new

            # ── Track moving markers ──
            if H is not None:
                for mid, c in undist_dict.items():
                    if mid in CORNER_IDS:
                        continue
                    cx = c[:, 0].mean()
                    cy = c[:, 1].mean()
                    mx, my = warp_point(H, cx, cy)

                    # Clamp inside window
                    mx = max(0, min(OUTPUT_WIN_PX - 1, mx))
                    my = max(0, min(OUTPUT_WIN_PX - 1, my))

                    tracked[mid] = (mx, my)
                    if mid not in trails:
                        trails[mid] = []
                    trails[mid].append((mx, my))
                    if len(trails[mid]) > MAX_TRAIL:
                        trails[mid].pop(0)

        # ── OSD on camera frame ──
        status_calib = "CALIB: OK" if calibrated else "CALIB: waiting for all 4 corners"
        status_homo  = "HOMO: OK"  if H is not None else "HOMO: waiting"
        cv2.putText(display, status_calib, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0) if calibrated else (0, 165, 255), 2)
        cv2.putText(display, status_homo,  (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0) if H is not None else (0, 165, 255), 2)

        # ── Windows ──
        cv2.imshow("Camera Feed", display)
        map_frame = draw_map(tracked, trails)
        cv2.imshow("Top-Down Map (1m x 1m)", map_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            H = None
            print("[INFO] Homography reset.")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()