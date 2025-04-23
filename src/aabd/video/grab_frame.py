import cv2
import os


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


class VideoToFrameIterator:

    def __init__(self, video_path, out_path=None, tqdm_enable=True,
                 start_time=None, end_time=None, min_interval_time=None,
                 start_frame=None, end_frame=None, min_interval_frame=None):

        self.video_path = video_path

        cap = cv2.VideoCapture(video_path)
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        frame_type = start_frame is not None or end_frame is not None or min_interval_frame is not None
        time_type = start_time is not None or end_time is not None or min_interval_time is not None

        if frame_type and time_type:
            raise Exception('frame and time types cannot be combined')
        elif frame_type:
            self.iterator_func = video_frame_iterator_by_frame
            self.iterator = self.iterator_func(video_path, min_interval_frame, start_frame, end_frame)
            end_frame = end_frame if end_frame is not None else self.frame_count
            start_frame = start_frame if start_frame is not None else 0
            min_interval = min_interval_frame if min_interval_frame is not None else 0
        elif time_type:
            self.iterator_func = video_frame_iterator_by_time
            self.iterator = self.iterator_func(video_path, min_interval_time, start_time, end_time)
            if end_time is not None:
                end_frame = end_time / 1000 * self.fps
            else:
                end_frame = self.frame_count
            if start_time is not None:
                start_frame = start_time / 1000 * self.fps
            else:
                start_frame = 0
            if min_interval_time is not None:
                min_interval = int(min_interval_time / 1000 * self.fps)
            else:
                min_interval = 0

        else:
            self.iterator_func = video_frame_iterator
            self.iterator = self.iterator_func(video_path)
            start_frame = 0
            end_frame = self.frame_count
            min_interval = 0

        self.length = int((end_frame - start_frame) // (min_interval + 1) + 1)

        if tqdm_enable:
            from tqdm import tqdm
            self.tqdm_c = tqdm(total=self.__len__(), unit='frame', desc=f'{os.path.basename(video_path)}')
        else:
            self.tqdm_c = None

        self.out_writer = self.__make_video_writer__(out_path) if out_path is not None else None

    def __enter__(self):
        if self.out_writer is not None:
            return self, self.out_writer
        else:
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            # 尝试发送停止信号，适用于协程或生成器
            self.iterator.send("stop")
            self.out_writer.release()
        except StopIteration:
            pass
        except AttributeError:
            # 如果迭代器不支持 .send() 方法，则忽略
            pass

    def __next__(self):
        data = next(self.iterator)
        if self.tqdm_c is not None:
            self.tqdm_c.update(1)
        return data

    def __iter__(self):
        return self

    def __len__(self):
        return self.length

    def __make_video_writer__(self, output_video_path):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        return cv2.VideoWriter(output_video_path, fourcc, self.fps, (self.width, self.height))


if __name__ == '__main__':
    from tqdm import tqdm
    import time

    v = r"D:\codes\projects\python240409\tennis\tennis.mkv"
    o = r"D:\codes\projects\python240409\tennis\tennis1.mkv"
    # with VideoToFrameIterator(v, min_interval_time=2000, start_time=20, end_time=99999,
    #                           tqdm_enable=True) as v:
    with VideoToFrameIterator(v, o, min_interval_frame=1, start_frame=0, end_frame=500,
                              tqdm_enable=True) as (v, o):
        for frame_index, current_time, frame in v:
            o.write(frame)
    # iter = video_frame_iterator_by_time(v, min_interval=60, start_time=0, end_time=1000)
    # with StreamManager(iter) as ss:
    #     for frame_index, current_time, frame in ss:
    #         print(frame_index)
