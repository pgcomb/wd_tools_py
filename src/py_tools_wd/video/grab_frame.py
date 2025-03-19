import cv2


def video_frame_iterator(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception(f"无法打开视频: {video_path}")
    try:
        # 获取总帧数
        fps = cap.get(cv2.CAP_PROP_FPS)

        frame_index = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # 计算当前帧的时间戳（毫秒）
            current_time = int(frame_index * 1000 / fps)
            status = yield frame_index, current_time, frame
            if status == 'stop':
                break
            frame_index += 1
    finally:
        cap.release()


def video_frame_iterator_by_time(video_path, min_interval=0, start_time=0, end_time=99999999):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception(f"无法打开视频: {video_path}")
    try:
        # 获取视频帧率和总帧数
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        start_frame = max(int(start_time * fps / 1000), 0)
        start_frame = min(start_frame, total_frames - 1)
        end_frame = int(end_time * fps / 1000)
        end_frame = max(start_frame, min(end_frame, total_frames - 1))
        # 根据fps和min_interval(ms)计算每帧之间的间隔帧数
        frame_skip = max(int(min_interval * fps / 1000) + 1, 1)

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        frame_index = start_frame
        while True:
            ret, frame = cap.read()
            if not ret or frame_index > end_frame:
                break

            # 计算当前帧的时间戳（毫秒）
            current_time = int(frame_index * 1000 / fps)

            # 如果当前帧满足跳帧条件，并且在指定的时间范围内，则返回该帧
            if frame_index % frame_skip == 0:
                status = yield frame_index, current_time, frame
                if status == 'stop':
                    break

            frame_index += 1
    finally:
        cap.release()


def video_frame_iterator_by_frame(video_path, min_interval=0, start_frame=0, end_frame=999999999):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception(f"无法打开视频: {video_path}")

    try:
        # 获取总帧数
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 如果没有提供开始和结束帧，则默认为整个视频的开始和结束
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = total_frames - 1  # 结束帧设为最后一帧的索引

        # 确保给定的起始和结束帧在有效范围内
        start_frame = max(0, min(start_frame, total_frames - 1))
        end_frame = max(start_frame, min(end_frame, total_frames - 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        min_interval = max(min_interval + 1, 1)
        frame_index = start_frame
        while True:
            ret, frame = cap.read()
            if not ret or frame_index > end_frame:
                break
            # 计算当前帧的时间戳（毫秒）
            current_time = int(frame_index * 1000 / fps)
            # 如果当前帧满足跳帧条件，并且在指定的帧范围之内，则返回该帧
            if (frame_index - start_frame) % min_interval == 0:
                status = yield frame_index, current_time, frame
                if status == 'stop':
                    break

            frame_index += 1
    finally:
        cap.release()


class StreamManager:

    def __init__(self, iterator):
        self.iterator = iterator

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            # 尝试发送停止信号，适用于协程或生成器
            self.iterator.send("stop")
        except StopIteration:
            pass
        except AttributeError:
            # 如果迭代器不支持 .send() 方法，则忽略
            pass

    def __next__(self):
        return next(self.iterator)

    def __iter__(self):
        return self


if __name__ == '__main__':
    v = "/data/videos/pingpong_250227/5105247089-20231215154838_sc99_01.mp4"
    iter = video_frame_iterator_by_time(v, min_interval=60, start_time=0, end_time=1000)
    with StreamManager(iter) as ss:
        for frame_index, current_time, frame in ss:
            print(frame_index)
