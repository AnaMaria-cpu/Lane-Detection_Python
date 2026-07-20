import cv2


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

    cv2.imshow("Original resized", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cam.release()
cv2.destroyAllWindows()