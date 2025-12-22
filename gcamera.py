import cv2
print(cv2.getBuildInformation())

gst_str = (
    "udpsrc port=5000 caps=\"application/x-rtp, media=video, encoding-name=H265, payload=96\" ! "
    "rtph265depay ! h265parse ! avdec_h265 ! videoconvert ! appsink"
)

cap = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("Не удалось открыть поток")
    exit(1)

while True:
    ret, frame = cap.read()
    if not ret:
        print(cv2.getBuildInformation())
        print("Не удалось прочитать кадр")
        break

    cv2.imshow("frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
