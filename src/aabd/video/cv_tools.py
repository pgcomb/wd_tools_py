import cv2


def video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return int(w), int(h), fps, int(frame_count)


def make_video_writer_from_video(video_path, output_video_path):
    w, h, fps, _ = video_info(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    return cv2.VideoWriter(output_video_path, fourcc, fps, (w, h))


if __name__ == '__main__':
    print(video_info(r"D:\Code\aigc-event-highlights\tennis\tennis.mkv"))
