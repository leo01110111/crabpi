#!/usr/bin/env python3
"""
Face position notifier.

Reads from the camera and prints the face position to the terminal:
face at left, face at center, face at right, or no face. No hardware required.
"""

import os
import sys
import time

# Silence Qt font-directory warnings from OpenCV's Qt backend (before cv2)
os.environ.setdefault('QT_LOGGING_RULES', '*.debug=false;qt.qpa.*=false')

import cv2  # noqa: E402


# Zone boundaries (fractions of frame width):
# left [0, 1/3), center [1/3, 2/3), right [2/3, 1]
LEFT_END = 1 / 3
RIGHT_START = 2 / 3


def get_face_position(face_center_x: float, frame_width: int) -> str:
    """Return 'left', 'center', or 'right' from face center X (mirrored)."""
    x_frac = face_center_x / frame_width
    if x_frac < LEFT_END:
        return 'right'
    if x_frac < RIGHT_START:
        return 'center'
    return 'left'


def main() -> None:
    """Run camera, detect face, print position (left/center/right/no face)."""
    try:
        cap = cv2.VideoCapture(0)
    except Exception as e:
        print(f'Error opening camera: {e}', file=sys.stderr)
        sys.exit(1)

    if not cap.isOpened():
        print('Could not open camera.', file=sys.stderr)
        sys.exit(1)

    cascade_path = (
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print('Failed to load face cascade.', file=sys.stderr)
        cap.release()
        sys.exit(1)

    show_window = '--window' in sys.argv
    if show_window:
        print(
            'Face position notifier — press "q" in camera window to quit.\n'
        )
    else:
        print('Face position notifier — Ctrl+C to stop.\n')

    last_state: str | None = None

    try:
        while True:
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

            if len(faces) == 0:
                state = 'no face'
            else:
                (fx, fy, fw, fh) = max(faces, key=lambda r: r[2] * r[3])
                center_x = fx + fw / 2
                state = f'face at {get_face_position(center_x, w)}'

            if state != last_state:
                last_state = state
                print(f'\r  >>> {state.upper()} <<<  ', end='', flush=True)

            if show_window:
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
                time.sleep(0.05)

    finally:
        cap.release()
        cv2.destroyAllWindows()

    print('\nDone.')


if __name__ == '__main__':
    main()
