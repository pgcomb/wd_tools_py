import os
import cv2
import random
import argparse
from threading import Thread
from queue import Queue
from tqdm import tqdm


def try_open_video(url, timeout=10):
    cap = cv2.VideoCapture(url)
    result_queue = Queue()

    def target():
        if cap.isOpened():
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            result_queue.put((cap, total_frames))
        else:
            result_queue.put((None, 0))

    thread = Thread(target=target)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        cap.release()
        return None, 0
    else:
        return result_queue.get()


def main():
    parser = argparse.ArgumentParser(description='Extract frames from videos')
    parser.add_argument('--input', '-i', type=str, default='video_list.txt',
                        help='Input file containing video URLs')
    parser.add_argument('--output', '-o', type=str, default='output_images',
                        help='Output directory for extracted frames')
    parser.add_argument('--frames', '-f', type=int, default=10,
                        help='Number of frames to extract per video')
    args = parser.parse_args()

    video_list_file = args.input
    output_root = args.output
    max_frames = args.frames

    with open(video_list_file, 'r') as f:
        video_urls = [line.strip() for line in f if line.strip()]

    for url in tqdm(video_urls, desc="Processing videos"):
        try:
            video_filename = os.path.basename(url)
            video_name = os.path.splitext(video_filename)[0]
            output_dir = os.path.join(output_root, video_name)

            os.makedirs(output_dir, exist_ok=True)

            existing_images = [f for f in os.listdir(output_dir)
                               if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            current_count = len(existing_images)

            if current_count >= max_frames:
                tqdm.write(f"Skipping {video_name}, already has {current_count} frames.")
                continue

            needed = max_frames - current_count

            selected_file = os.path.join(output_dir, 'selected_frames.txt')
            selected_frames = []
            if os.path.exists(selected_file):
                with open(selected_file, 'r') as f:
                    selected_frames = [int(line.strip()) for line in f]
            else:
                with open(selected_file, 'w') as f:
                    pass

            cap, total_frames = try_open_video(url, timeout=10)
            if not cap or total_frames <= 0:
                tqdm.write(f"Failed to open video {url} within timeout or no frames available")
                continue

            available_frames = list(set(range(total_frames)) - set(selected_frames))
            if len(available_frames) < needed:
                needed = len(available_frames)
                if needed <= 0:
                    cap.release()
                    continue

            new_selected = random.sample(available_frames, needed)
            selected_frames.extend(new_selected)

            with open(selected_file, 'a') as f:
                for frame in new_selected:
                    f.write(f"{frame}\n")

            for frame_num in new_selected:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                if not ret:
                    tqdm.write(f"Failed to read frame {frame_num} from {url}")
                    continue
                img_path = os.path.join(output_dir, f"{video_name}_{frame_num}.jpg")
                cv2.imwrite(img_path, frame)

            cap.release()

        except Exception as e:
            tqdm.write(f"Error processing {url}: {str(e)}")
            continue


if __name__ == "__main__":
    main()
