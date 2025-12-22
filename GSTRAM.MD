```bash

gst-launch-1.0 \
rtspsrc location=rtsp://admin:nurs1905@192.168.1.64/stream ! \
rtph265depay ! h265parse ! rtph265pay pt=96 ! \
udpsink host=100.108.121.62 port=5000

```