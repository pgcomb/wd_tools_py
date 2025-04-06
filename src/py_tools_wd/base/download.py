import os
from tqdm import tqdm
import requests
import sys

def download_files(download_file_path, download_dir):
    timeout = 10

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    def download_file(url, global_bar=None):
        local_filename = os.path.join(download_dir, url.split('/')[-1])
        try:
            response = requests.head(url, timeout=timeout)
            file_size = int(response.headers.get('content-length', 0))
            if file_size == 0:
                print(f"文件 {url} 无效，跳过")
                return 0  # 不计入进度

            if os.path.exists(local_filename):
                existing_size = os.path.getsize(local_filename)
                if existing_size >= file_size:
                    print(f"文件 {local_filename} 已存在，跳过")
                    return 0  # 不计入进度
            else:
                existing_size = 0

            headers = {"Range": f"bytes={existing_size}-"}
            req = requests.get(url, headers=headers, stream=True, timeout=timeout)
            total = file_size - existing_size

            with open(local_filename, 'ab') as f, \
                    tqdm(
                        total=total,
                        initial=0,
                        unit='B',
                        unit_scale=True,
                        desc=local_filename.split('/')[-1],
                        position=1,
                        mininterval=0.1,
                        leave=True
                    ) as bar:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
                return 1  # 成功下载，返回1

        except requests.RequestException as e:
            print(f"下载失败：{url} 错误信息：{e}")
            return 0  # 下载失败，不计入进度

    if not os.path.exists(download_file_path):
        print(f"下载链接文件 {download_file_path} 不存在！")
        return

    with open(download_file_path, 'r') as f:
        urls = [url.strip() for url in f.readlines() if url.strip()]

    # 计算需要下载的文件总数
    total_files = 0
    for url in urls:
        local_filename = os.path.join(download_dir, url.split('/')[-1])
        try:
            response = requests.head(url, timeout=timeout)
            file_size = int(response.headers.get('content-length', 0))
            if file_size == 0:
                continue

            if os.path.exists(local_filename):
                existing_size = os.path.getsize(local_filename)
                if existing_size >= file_size:
                    continue  # 已存在，不计入总数
            total_files += 1
        except requests.RequestException as e:
            print(f"获取文件信息失败：{url}，错误：{e}")
            continue

    # 创建全局进度条（按文件数量）
    with tqdm(
        total=total_files,
        unit='文件',
        desc="全局进度",
        position=0,
        mininterval=0.1,
        leave=True
    ) as global_bar:
        for url in urls:
            if not url.strip():
                continue
            res = download_file(url, global_bar)
            global_bar.update(res)

def main():
    default_download_file = './downloads.txt'
    default_download_dir = './output'

    if len(sys.argv) > 1:
        download_file_path = sys.argv[1]
    else:
        download_file_path = default_download_file

    if len(sys.argv) > 2:
        download_dir = sys.argv[2]
    else:
        download_dir = default_download_dir

    download_files(download_file_path, download_dir)

if __name__ == "__main__":
    main()