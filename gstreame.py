import cv2

rtsp_url = "rtsp://admin:nurs1905@192.168.1.64:554/Streaming/Channels/102"

gst = (
    f"rtspsrc location={rtsp_url} latency=0 ! "
    "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink"
)

cap = cv2.VideoCapture(gst, cv2.CAP_GSTREAMER)

while True:
    ret, frame = cap.read()
    if not ret:
        print("no frame")
        continue

    cv2.imshow("Camera", frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()