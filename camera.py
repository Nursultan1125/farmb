import cv2

# --- ВАШ RTSP ПОТОК ---
rtsp_url = "rtsp://admin:nurs1905@192.168.1.64:554/Streaming/Channels/101"

# --- Открываем поток ---
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("Не удалось открыть поток.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Ошибка чтения кадра")
        break

    cv2.imshow("IP Camera", frame)

    # закрыть окно по нажатию ESC
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
