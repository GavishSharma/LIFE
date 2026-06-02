import cv2
import sys

def main():
    print("Initializing camera feed...")
    # Initialize the camera (0 is usually the default built-in camera or external USB camera)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam. Make sure your camera is connected and not being used by another application.")
        sys.exit(1)

    # Set camera resolution (optional, but good for performance)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Choose ArUco dictionary (DICT_4X4_50 to match user's 80mm ID 0 marker)
    # We use a try-except structure to support both newer (OpenCV 4.7+) and older versions of OpenCV
    try:
        # OpenCV 4.7.0+ API
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)
        has_new_api = True
        print("Using OpenCV 4.7.0+ ArucoDetector API (DICT_4X4_50)")
    except AttributeError:
        # OpenCV < 4.7.0 API
        dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters_create()
        has_new_api = False
        print("Using legacy OpenCV ArUco API (DICT_4X4_50)")

    print("\n--- Detection Started ---")
    print("Press 'q' key to quit the program.")

    while True:
        # Capture frame-by-frameimport cv2
import sys
import math

def main():
    print("Initializing camera feed...")
    # Initialize the camera (0 is usually the default built-in camera or external USB camera)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam. Make sure your camera is connected and not being used by another application.")
        sys.exit(1)

    # Set camera resolution (optional, but good for performance)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Choose ArUco dictionary (DICT_4X4_50 to match user's 80mm ID 0 marker)
    # We use a try-except structure to support both newer (OpenCV 4.7+) and older versions of OpenCV
    try:
        # OpenCV 4.7.0+ API
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)
        has_new_api = True
        print("Using OpenCV 4.7.0+ ArucoDetector API (DICT_4X4_50)")
    except AttributeError:
        # OpenCV < 4.7.0 API
        dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters_create()
        has_new_api = False
        print("Using legacy OpenCV ArUco API (DICT_4X4_50)")

    print("\n--- Detection Started ---")
    print("Press 'q' key to quit the program.")

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        # Detect markers
        if has_new_api:
            corners, ids, rejected = detector.detectMarkers(frame)
        else:
            corners, ids, rejected = cv2.aruco.detectMarkers(frame, dictionary, parameters=parameters)

        # If markers are detected, process and draw them
        if ids is not None:
            # Draw borders and lines around the detected markers
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            
            # Label each marker with its ID and orientation on the screen
            for i in range(len(ids)):
                marker_corners = corners[i][0]
                
                # Corner coordinates:
                # 0: Top-Left, 1: Top-Right, 2: Bottom-Right, 3: Bottom-Left
                c0 = marker_corners[0] # Top-Left
                c1 = marker_corners[1] # Top-Right
                c2 = marker_corners[2] # Bottom-Right
                c3 = marker_corners[3] # Bottom-Left
                
                # Calculate center of the marker
                cx = int((c0[0] + c1[0] + c2[0] + c3[0]) / 4)
                cy = int((c0[1] + c1[1] + c2[1] + c3[1]) / 4)
                
                # Calculate the center of the top edge (front of the marker)
                tx = int((c0[0] + c1[0]) / 2)
                ty = int((c0[1] + c1[1]) / 2)
                
                # Vector pointing "forward" from center to top edge
                vx = tx - cx
                vy = ty - cy
                
                # In OpenCV, Y-axis points down, so we invert the Y vector component
                # to align with standard math where Up is positive Y.
                angle_rad = math.atan2(-vy, vx)
                angle_deg = int(math.degrees(angle_rad) % 360)
                
                # Draw a red arrow pointing in the forward direction
                cv2.arrowedLine(frame, (cx, cy), (tx, ty), (0, 0, 255), 3, tipLength=0.3)
                
                # Draw a blue dot at the center
                cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                
                # Print detected ID and Angle in the console
                print(f"Marker ID: {ids[i][0]} | Orientation: {angle_deg}°")
                
                # Label ID and Angle text next to the marker
                text_x = int(c0[0])
                text_y = int(c0[1]) - 15
                
                cv2.putText(
                    frame,
                    f"ID: {ids[i][0]} | {angle_deg}deg",
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0), # Green color
                    2,
                    cv2.LINE_AA
                )

        # Display the resulting frame
        cv2.imshow("ArUco Marker Detector", frame)

        # Break the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Clean up and close all windows
    cap.release()
    cv2.destroyAllWindows()
    print("Camera released. Exiting program.")

if __name__ == "__main__":
    main()

        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        # Detect markers
        if has_new_api:
            corners, ids, rejected = detector.detectMarkers(frame)
        else:
            corners, ids, rejected = cv2.aruco.detectMarkers(frame, dictionary, parameters=parameters)

        # If markers are detected, process and draw them
        if ids is not None:
            # Draw borders and lines around the detected markers
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            
            # Print detected marker IDs in the console
            print(f"Detected Marker ID(s): {ids.flatten()}")
            
            # Label each marker with its ID on the screen
            for i in range(len(ids)):
                # Calculate the center or top-left corner of the marker to place the text
                marker_corners = corners[i][0]
                top_left = (int(marker_corners[0][0]), int(marker_corners[0][1]))
                
                # Add text to the image
                cv2.putText(
                    frame,
                    f"ID: {ids[i][0]}",
                    (top_left[0], top_left[1] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0), # Green color
                    2,
                    cv2.LINE_AA
                )

        # Display the resulting frame
        cv2.imshow("ArUco Marker Detector", frame)

        # Break the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Clean up and close all windows
    cap.release()
    cv2.destroyAllWindows()
    print("Camera released. Exiting program.")

if __name__ == "__main__":
    main()
