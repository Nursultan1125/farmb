import cv2

rtsp_url = "rtsp://admin:nurs1905@192.168.1.64:554/Streaming/Channels/101"

# Отключаем буфер (важно!)
gst = (
    f"rtspsrc location={rtsp_url} latency=0 ! "
    "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink"
)

cap = cv2.VideoCapture(gst, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("❌ Не могу открыть RTSP поток")
    exit()

print("✅ RTSP открыт! Начинаю чтение кадров...")

while True:
    ret, frame = cap.read()

    if not ret or frame is None:
        print("no frame")
        continue

    cv2.imshow("IP Camera", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
