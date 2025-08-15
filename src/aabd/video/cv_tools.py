import time
from threading import Thread

import cv2


def video_info(video_path, timeout=5000):
    data = []
    def func():
        cap = cv2.VideoCapture(video_path)
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        data.append((int(w), int(h), fps, int(frame_count)))
    Thread(target=func).start()
    start_time = time.time()
    while time.time() - start_time < timeout / 1000:
        if len(data) > 0:
            return data[0]
        else:
            time.sleep(0.01)
    raise Exception("read video timeout")


def make_video_writer_from_video(video_path, output_video_path):
    w, h, fps, _ = video_info(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    return cv2.VideoWriter(output_video_path, fourcc, fps, (w, h))


if __name__ == '__main__':
    print(time.time())
    try:
        print(video_info(r"rtmp://192.168.0.16:1935/video/wdx111", timeout=5000))
    except:
        pass
    print(time.time())
