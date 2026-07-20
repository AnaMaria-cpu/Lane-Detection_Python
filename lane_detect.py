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
    for row in range(height):
        for column in range(width):
            blue = frame[row, column, 0]
            green = frame[row, column, 1]
            red = frame[row, column, 2]

            gray_value = int(
                0.114 * blue +
                0.587 * green +
                0.299 * red
            )

            gray_frame[row, column] = gray_value

    # TASK 4: selectăm doar zona drumului

    upper_right = (int(width * 0.52), int(height * 0.76))
    upper_left = (int(width * 0.45), int(height * 0.76))
    lower_left = (0, height - 1)
    lower_right = (width - 1, height - 1)

    trapezoid_points = np.array(
        [upper_right, upper_left, lower_left, lower_right],
        dtype=np.int32
    )

    trapezoid_frame = np.zeros((height, width), dtype=np.uint8)

    cv2.fillConvexPoly(
        trapezoid_frame,
        trapezoid_points,
        1
    )

    road_frame = gray_frame * trapezoid_frame

    # TASK 5: transformăm drumul într-o vedere de sus

    # Colțurile întregului frame, în aceeași ordine ca trapezul:
    # upper right, upper left, lower left, lower right
    frame_points = np.array(
        [
            (width - 1, 0),
            (0, 0),
            (0, height - 1),
            (width - 1, height - 1)
        ],
        dtype=np.float32
    )

    trapezoid_points_float = np.float32(trapezoid_points)

    perspective_matrix = cv2.getPerspectiveTransform(
        trapezoid_points_float,
        frame_points
    )

    top_down_frame = cv2.warpPerspective(
        road_frame,
        perspective_matrix,
        (width, height)
    )
    # TASK 6: aplicăm blur pe imaginea văzută de sus
    blurred_frame = cv2.blur(
        top_down_frame,
        ksize=(5, 5)
    )



    cv2.imshow("Original resized", frame)
    cv2.imshow("Grayscale manual", gray_frame)
    cv2.imshow("Trapezoid", trapezoid_frame * 255)
    cv2.imshow("Road only", road_frame)
    cv2.imshow("Top down", top_down_frame)
    cv2.imshow("Blurred", blurred_frame)
    
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()
