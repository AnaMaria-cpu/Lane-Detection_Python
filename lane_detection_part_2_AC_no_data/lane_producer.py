import cv2
import object_socket


video_path = r"D:\Aumovio\sapt2_Python\Lane-Detection_Python\Lane Detection Test Video 01.mp4"

video = cv2.VideoCapture(video_path)

if not video.isOpened():
    raise FileNotFoundError(
        f'Videoclipul "{video_path}" nu a putut fi deschis.'
    )

# Creează socketul care trimite frame-urile.
s = object_socket.ObjectSenderSocket(
    '127.0.0.1',
    5000,
    print_when_awaiting_receiver=True,
    print_when_sending_object=True
)

try:
    while True:
        # Citim un frame din videoclip.
        ret, frame = video.read()

        try:
            # Trimitem către consumer rezultatul citirii și frame-ul.
            s.send_object((ret, frame))
        except (BrokenPipeError, ConnectionResetError):
            print("Consumerul s-a închis.")
            break

        # Dacă videoclipul s-a terminat, ieșim.
        if not ret:
            break

finally:
    video.release()

    if s.is_connected():
        s.close()

    s.sock.close()

print("Producerul s-a închis.")