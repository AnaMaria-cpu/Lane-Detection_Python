import cv2
import numpy as np

cam = cv2.VideoCapture("Lane Detection Test Video 01.mp4")

first_frame = True

# Punctele liniilor din cadrul anterior
left_top = (0, 0)
left_bottom = (0, 0)

right_top = (0, 0)
right_bottom = (0, 0)

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

    # TASK 7: detectarea marginilor cu filtre Sobel

    # Filtrul Sobel pentru diferențe pe orizontală
    sobel_vertical = np.array(
        [
            [-1, -2, -1],
            [0, 0, 0],
            [+1, +2, +1]
        ],
        dtype=np.float32
    )

    sobel_horizontal = np.transpose(sobel_vertical)

    # Convertim imaginea la float32 pentru a putea avea și valori negative
    blurred_float = np.float32(blurred_frame)

    # Aplicăm separat cele două filtre pe aceeași imagine
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

    # Combinăm cele două rezultate
    sobel_combined = np.sqrt(
        horizontal_edges ** 2 +
        vertical_edges ** 2
    )

    # Convertim rezultatul înapoi la uint8 pentru afișare
    sobel_frame = cv2.convertScaleAbs(sobel_combined)

    # TASK 8: binarizarea imaginii

    threshold = int(255 / 2)  # 127

    binary_frame = sobel_frame.copy()

    binary_frame[binary_frame < threshold] = 0

    binary_frame[binary_frame >= threshold] = 255

    # TASK 9: găsim coordonatele marcajelor din stânga și dreapta

    # Facem o copie ca să nu modificăm binary_frame
    clean_binary_frame = binary_frame.copy()

    side_margin = int(width * 0.05)

    clean_binary_frame[:, :side_margin] = 0
    clean_binary_frame[:, width - side_margin:] = 0

    middle = width // 2

    left_half = clean_binary_frame[:, :middle]
    right_half = clean_binary_frame[:, middle:]

    # np.argwhere returnează coordonatele în ordinea (row, column), adică (y, x)
    left_points = np.argwhere(left_half == 255)
    right_points = np.argwhere(right_half == 255)

    # Separăm coordonatele pentru partea stângă
    left_y = left_points[:, 0]
    left_x = left_points[:, 1]

    # Separăm coordonatele pentru partea dreaptă
    right_y = right_points[:, 0]
    right_x = right_points[:, 1] + middle

    # TASK 10: găsim liniile care se potrivesc marcajelor

    # Calculăm linia din partea stângă
    if len(left_x) >= 2:

        # polyfit returnează b și a pentru ecuația:
        # y = a * x + b
        left_b, left_a = np.polynomial.polynomial.polyfit(
            left_x,
            left_y,
            deg=1
        )

        # Evităm împărțirea la zero
        if abs(left_a) > 0.0001:

            left_top_x = int((0 - left_b) / left_a)
            left_bottom_x = int(((height - 1) - left_b) / left_a)

            # Actualizăm punctele doar dacă valorile sunt valide
            if (
                    0 <= left_top_x < width
                    and 0 <= left_bottom_x < width
            ):
                left_top = (left_top_x, 0)
                left_bottom = (left_bottom_x, height - 1)

    # Calculăm linia din partea dreaptă
    if len(right_x) >= 2:

        right_b, right_a = np.polynomial.polynomial.polyfit(
            right_x,
            right_y,
            deg=1
        )

        if abs(right_a) > 0.0001:

            right_top_x = int((0 - right_b) / right_a)
            right_bottom_x = int(((height - 1) - right_b) / right_a)

            if (
                    0 <= right_top_x < width
                    and 0 <= right_bottom_x < width
            ):
                right_top = (right_top_x, 0)
                right_bottom = (right_bottom_x, height - 1)

    # Transformăm imaginea binară în imagine cu 3 canale
    # doar pentru a putea desena liniile în culori diferite
    lane_lines_frame = cv2.cvtColor(
        clean_binary_frame,
        cv2.COLOR_GRAY2BGR
    )

    # Linia din stânga - albastră
    cv2.line(
        lane_lines_frame,
        left_top,
        left_bottom,
        (255, 0, 0),
        5
    )

    # Linia din dreapta - roșie
    cv2.line(
        lane_lines_frame,
        right_top,
        right_bottom,
        (0, 0, 255),
        5
    )

    # Linia care separă cele două jumătăți
    cv2.line(
        lane_lines_frame,
        (middle, 0),
        (middle, height - 1),
        (255, 255, 0),
        1
    )

    cv2.imshow("Original resized", frame)
    cv2.imshow("Grayscale manual", gray_frame)
    cv2.imshow("Trapezoid", trapezoid_frame * 255)
    cv2.imshow("Road only", road_frame)
    cv2.imshow("Top down", top_down_frame)
    cv2.imshow("Blurred", blurred_frame)

    cv2.imshow("Sobel horizontal",cv2.convertScaleAbs(horizontal_edges))
    cv2.imshow("Sobel vertical",cv2.convertScaleAbs(vertical_edges) )
    cv2.imshow("Sobel combined", sobel_frame)

    cv2.imshow("Binarized", binary_frame)

    cv2.imshow("Lane lines", lane_lines_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()
