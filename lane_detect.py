import cv2
import numpy as np

cam = cv2.VideoCapture("Lane Detection Test Video 01.mp4")

first_frame = True

while True:
    ret, frame = cam.read()

    if ret is False:
        break

    if first_frame is True:
        print("dimensiune originală =", frame.shape)
        first_frame = False
    frame = cv2.resize(frame, (480, 270))
    height, width, channels = frame.shape

    # TASK 3: creăm manual o imagine grayscale goală
    gray_frame = np.zeros((height, width), dtype=np.uint8)
    # Parcurgem fiecare pixel
    for row in range(height):
        for column in range(width):
            blue = frame[row, column, 0]
            green = frame[row, column, 1]
            red = frame[row, column, 2]

            # Transformăm cele 3 culori într-o singură valoare grayscale
            gray_value = int(
                0.114 * blue +
                0.587 * green +
                0.299 * red
            )

            gray_frame[row, column] = gray_value


    cv2.imshow("Original resized", frame)
    cv2.imshow("Grayscale manual", gray_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cam.release()
cv2.destroyAllWindows()