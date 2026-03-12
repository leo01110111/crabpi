#!/usr/bin/env python3
"""
Eye follower: drive 7-segment eyes from camera face position.

Reads from the camera, detects face position (left/center/right), and updates
EyeControl so the eyes look left, right, or forward. Supports blink and
sleep (eyes off when no face for a while).
"""

import os
import sys
import time
from eye_control import EyeControl

# Silence Qt font-directory warnings from OpenCV's Qt backend
os.environ.setdefault('QT_LOGGING_RULES', '*.debug=false;qt.qpa.*=false')

import cv2


# Zone boundaries (fractions of frame width):
# left [0, 1/3), center [1/3, 2/3), right [2/3, 1]
LEFT_END = 1 / 3
RIGHT_START = 2 / 3


def get_face_position(face_center_x: float, frame_width: int) -> str:
    """Return 'left', 'center', or 'right' based on face center X (mirrored)."""
    x_frac = face_center_x / frame_width
    if x_frac < LEFT_END:
        return 'right'
    if x_frac < RIGHT_START:
        return 'center'
    return 'left'


def main() -> None:
    """Run camera, detect face, print position state (left/center/right/no face)."""
    try:
        cap = cv2.VideoCapture(0)
    except Exception as e:
        print(f'Error opening camera: {e}', file=sys.stderr)
        sys.exit(1)

    if not cap.isOpened():
        print('Could not open camera.', file=sys.stderr)
        sys.exit(1)

    # Prefer Haar cascade (bundled with OpenCV, no extra files on Pi)
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print('Failed to load face cascade.', file=sys.stderr)
        cap.release()
        sys.exit(1)

    show_window = '--window' in sys.argv
    debug = '--debug' in sys.argv
    if show_window:
        print('Eye Follower — press "q" in the camera window to quit.\n')
    else:
        print('Eye Follower — Ctrl+C to quit.\n')

    last_state: str | None = None
    
    eye_control = EyeControl(17, 27, 22)
    eye_control.look_forward()
    sleep_counter = 0
    SLEEP_TIME = 10 #Number of iterations to trigger closed eyes
    BLINK_CYCLE = 10 #Number of iterations to trigger a blink
    blink_count = 0
    delay_per_iteration = 0.1 #Time to sleep between iterations
    
    try:
        while True:
            #=================== Read frame and detect faces ===================
            ok, frame = cap.read()
            if not ok:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
            )

            h, w = frame.shape[:2]

            #=================== Eye Control ===================
            if len(faces) == 0:
                state = 'no face'
                if last_state != 'no face':
                    sleep_counter = 1
                else:
                    sleep_counter += 1
                if sleep_counter > SLEEP_TIME:
                    eye_control.look_off()
                last_state = state
            else:  # There's a face
                # Use the largest face (first after sorting by area)
                (fx, fy, fw, fh) = max(faces, key=lambda r: r[2] * r[3])
                center_x = fx + fw / 2
                state = f'face at {get_face_position(center_x, w)}'

                if state != last_state:
                    last_state = state
                    if debug:
                        print(f'\r  >>> {state.upper()} <<<  ', end='', flush=True)
                    if (state == 'face at left'):
                        eye_control.look_left()
                    elif (state == 'face at right'):
                        eye_control.look_right()
                    else:
                        eye_control.look_forward()
            
            # If it's time to blink, close then restore on next iteration
            blink_count += 1
            if blink_count > BLINK_CYCLE and state != 'no face':
                blink_count = 0
                eye_control.look_closed()
                last_state = None  # Force re-apply of look next iteration

            #=================== Show window (if enabled) ===================
            if show_window:
                # Draw zone lines and face box
                cv2.line(
                    frame,
                    (int(w * LEFT_END), 0),
                    (int(w * LEFT_END), h),
                    (80, 80, 80),
                    1,
                )
                cv2.line(
                    frame,
                    (int(w * RIGHT_START), 0),
                    (int(w * RIGHT_START), h),
                    (80, 80, 80),
                    1,
                )
                for (fx, fy, fw, fh) in faces:
                    cv2.rectangle(
                        frame, (fx, fy), (fx + fw, fy + fh), (0, 255, 0), 2
                    )
                cv2.imshow('Face position', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.05)  # Reduce CPU use on Pi when no window
            
            time.sleep(delay_per_iteration)

    finally:
        cap.release()
        cv2.destroyAllWindows()
        eye_control.close()

    print('\nDone.')


if __name__ == '__main__':
    main()
