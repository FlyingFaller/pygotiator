import cv2
import collections

cam_index = 0 
cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 540)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)

frame_buffer = collections.deque(maxlen=90)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame. Exiting ...")
        break

    # Denoise so we can focuse on the pure bubbles
    blurred_frame = cv2.GaussianBlur(frame, (21, 21), 0)

    # Add newest frame to buffer
    frame_buffer.append(blurred_frame)

    # Wait for buffer to fill
    if len(frame_buffer) == frame_buffer.maxlen:
        
        # oldest frame is at index 0; newest is the one we just appended
        oldest_frame = frame_buffer[0]
        newest_frame = blurred_frame

        # Image delta
        delta = cv2.absdiff(oldest_frame, newest_frame)

        # This converts the faint ghosting into a stark black & white motion map
        gray_delta = cv2.cvtColor(delta, cv2.COLOR_BGR2GRAY)
        _, thresh_delta = cv2.threshold(gray_delta, 25, 255, cv2.THRESH_BINARY)

        cv2.imshow('Motion Map', thresh_delta)

    # Show the raw feed so you can ensure the camera hasn't frozen
    cv2.imshow('Live View', frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()