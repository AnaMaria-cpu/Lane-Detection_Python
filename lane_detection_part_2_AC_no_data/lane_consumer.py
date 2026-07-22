import cv2
import numpy as np
import object_socket


# Ne conectăm la producer și primim frame-urile.
s = object_socket.ObjectReceiverSocket(
    '127.0.0.1',
    5000,
    print_when_connecting_to_sender=True,
    print_when_receiving_object=True
)

first_frame = True

# Punctele liniilor initiale
left_top = (0, 0)
left_bottom = (0, 0)

right_top = (0, 0)
right_bottom = (0, 0)

while True:
    # Primim frame-ul de la lane_producer.py
    ret, frame = s.recv_object()

    if ret is False:
        break

    if first_frame is True:
        print("dimensiune originală =", frame.shape)
        first_frame = False

    frame = cv2.resize(frame, (480, 270))
    height, width, channels = frame.shape

    # imagine grayscale creată manual
    gray_frame = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    for row in range(height):
        for column in range(width):
            blue = frame[row, column, 0]
            green = frame[row, column, 1]
            red = frame[row, column, 2]

            gray_value = int(
                0.114 * blue
                + 0.587 * green
                + 0.299 * red
            )

            gray_frame[row, column] = gray_value

    #selectăm doar zona drumului
    upper_right = (
        int(width * 0.52),
        int(height * 0.76)
    )

    upper_left = (
        int(width * 0.45),
        int(height * 0.76)
    )

    lower_left = (0, height - 1)
    lower_right = (width - 1, height - 1)

    trapezoid_points = np.array(
        [
            upper_right,
            upper_left,
            lower_left,
            lower_right
        ],
        dtype=np.int32
    )

    trapezoid_frame = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    cv2.fillConvexPoly(
        trapezoid_frame,
        trapezoid_points,
        1
    )

    road_frame = gray_frame * trapezoid_frame

    #transformăm drumul într-o vedere de sus
    frame_points = np.array(
        [
            (width - 1, 0),
            (0, 0),
            (0, height - 1),
            (width - 1, height - 1)
        ],
        dtype=np.float32
    )

    trapezoid_points_float = np.float32(
        trapezoid_points
    )

    perspective_matrix = cv2.getPerspectiveTransform(
        trapezoid_points_float,
        frame_points
    )

    top_down_frame = cv2.warpPerspective(
        road_frame,
        perspective_matrix,
        (width, height)
    )

    # TASK 6: aplicăm blur
    blurred_frame = cv2.blur(
        top_down_frame,
        ksize=(5, 5)
    )

    # TASK 7: filtre Sobel
    sobel_vertical = np.array(
        [
            [-1, -2, -1],
            [0, 0, 0],
            [1, 2, 1]
        ],
        dtype=np.float32
    )

    sobel_horizontal = np.transpose(
        sobel_vertical
    )

    blurred_float = np.float32(
        blurred_frame
    )

    horizontal_edges = cv2.filter2D(
        blurred_float,
        -1,
        sobel_horizontal
    )

    vertical_edges = cv2.filter2D(
        blurred_float,
        -1,
        sobel_vertical
    )

    sobel_combined = np.sqrt(
        horizontal_edges ** 2
        + vertical_edges ** 2
    )

    sobel_frame = cv2.convertScaleAbs(
        sobel_combined
    )

    #binarizarea imaginii
    threshold = int(255 / 2)

    binary_frame = sobel_frame.copy()

    binary_frame[
        binary_frame < threshold
    ] = 0

    binary_frame[
        binary_frame >= threshold
    ] = 255

    #coordonatele marcajelor
    clean_binary_frame = binary_frame.copy()

    side_margin = int(width * 0.05)

    clean_binary_frame[
        :,
        :side_margin
    ] = 0

    clean_binary_frame[
        :,
        width - side_margin:
    ] = 0

    middle = width // 2

    left_half = clean_binary_frame[:, :middle]
    right_half = clean_binary_frame[:, middle:]

    left_points = np.argwhere(
        left_half == 255
    )

    right_points = np.argwhere(
        right_half == 255
    )

    left_y = left_points[:, 0]
    left_x = left_points[:, 1]

    right_y = right_points[:, 0]
    right_x = right_points[:, 1] + middle

    #liniile marcajelor
    if len(left_x) >= 2:
        left_b, left_a = (
            np.polynomial.polynomial.polyfit(
                left_x,
                left_y,
                deg=1
            )
        )

        if abs(left_a) > 0.0001:
            left_top_x = int(
                (0 - left_b) / left_a
            )

            left_bottom_x = int(
                ((height - 1) - left_b)
                / left_a
            )

            if (
                0 <= left_top_x < width
                and 0 <= left_bottom_x < width
            ):
                left_top = (
                    left_top_x,
                    0
                )

                left_bottom = (
                    left_bottom_x,
                    height - 1
                )

    if len(right_x) >= 2:
        right_b, right_a = (
            np.polynomial.polynomial.polyfit(
                right_x,
                right_y,
                deg=1
            )
        )

        if abs(right_a) > 0.0001:
            right_top_x = int(
                (0 - right_b) / right_a
            )

            right_bottom_x = int(
                ((height - 1) - right_b)
                / right_a
            )

            if (
                0 <= right_top_x < width
                and 0 <= right_bottom_x < width
            ):
                right_top = (
                    right_top_x,
                    0
                )

                right_bottom = (
                    right_bottom_x,
                    height - 1
                )

    lane_lines_frame = cv2.cvtColor(
        clean_binary_frame,
        cv2.COLOR_GRAY2BGR
    )

    cv2.line(
        lane_lines_frame,
        left_top,
        left_bottom,
        (255, 0, 0),
        5
    )

    cv2.line(
        lane_lines_frame,
        right_top,
        right_bottom,
        (0, 0, 255),
        5
    )

    cv2.line(
        lane_lines_frame,
        (middle, 0),
        (middle, height - 1),
        (255, 255, 0),
        1
    )

    #liniile peste cadrul original
    left_line_frame = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    cv2.line(
        left_line_frame,
        left_top,
        left_bottom,
        255,
        3
    )

    reverse_perspective_matrix = (
        cv2.getPerspectiveTransform(
            frame_points,
            trapezoid_points_float
        )
    )

    left_line_trapezoid = cv2.warpPerspective(
        left_line_frame,
        reverse_perspective_matrix,
        (width, height)
    )

    left_line_coordinates = np.argwhere(
        left_line_trapezoid > 0
    )

    right_line_frame = np.zeros(
        (height, width),
        dtype=np.uint8
    )

    cv2.line(
        right_line_frame,
        right_top,
        right_bottom,
        255,
        3
    )

    right_line_trapezoid = cv2.warpPerspective(
        right_line_frame,
        reverse_perspective_matrix,
        (width, height)
    )

    right_line_coordinates = np.argwhere(
        right_line_trapezoid > 0
    )

    final_frame = frame.copy()

    final_frame[
        left_line_coordinates[:, 0],
        left_line_coordinates[:, 1]
    ] = (50, 50, 250)

    final_frame[
        right_line_coordinates[:, 0],
        right_line_coordinates[:, 1]
    ] = (50, 250, 50)

    cv2.imshow(
        "Final lane detection",
        final_frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

s.close()
cv2.destroyAllWindows()

print("Consumerul s-a închis.")