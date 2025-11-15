import cv2

rtsp_url = "rtsp://admin:nurs1905@192.168.1.64:554/Streaming/Channels/101"

# GStreamer pipeline для H.265 / HEVC
gst = (
    f"rtspsrc location={rtsp_url} latency=0 ! "
    "rtph265depay ! h265parse ! avdec_h265 ! "
    "videoconvert ! appsink"
)

cap = cv2.VideoCapture(gst, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("❌ Не могу открыть RTSP поток")
    exit()

print("✅ RTSP поток открыт (H.265)!")

while True:
    ret, frame = cap.read()

    if not ret or frame is None:
        print("no frame")
        continue

    cv2.imshow("IP Camera (H265)", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
