import inspect
import os
from pathlib import Path


def path_from_caller(module):
    if module and hasattr(module, '__file__'):
        directory = Path(module.__file__).resolve().parent
        return directory
    else:
        return None


def path_from_cwd():
    return Path.cwd()


def path_from_project():
    # 获取项目根目录 环境变量 PROJECT_ROOT
    path = os.environ.get('PROJECT_ROOT', None)
    if path is not None:
        return Path(path)
    return None


def to_absolute_path(path):
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    caller_path = path_from_caller(module)
    cwd_path = path_from_cwd()
    project_path = path_from_project()
    # print(caller_path)
    # print(cwd_path)
    # print(project_path)
    if caller_path is not None:
        abs_path = caller_path / path
        if abs_path.exists():
            return abs_path

    if cwd_path is not None:
        abs_path = cwd_path / path
        if abs_path.exists():
            return abs_path

    if project_path is not None:
        abs_path = project_path / path
        if abs_path.exists():
            return abs_path

    return None


def to_absolute_path_str(path):
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    caller_path = path_from_caller(module)
    cwd_path = path_from_cwd()
    project_path = path_from_project()
    # print(caller_path)
    # print(cwd_path)
    # print(project_path)
    if caller_path is not None:
        abs_path = caller_path / path
        if abs_path.exists():
            return abs_path.as_posix()

    if cwd_path is not None:
        abs_path = cwd_path / path
        if abs_path.exists():
            return abs_path.as_posix()

    if project_path is not None:
        abs_path = project_path / path
        if abs_path.exists():
            return abs_path.as_posix()

    return None


import os


def list_files(paths, suffixes=None, absolute=True):
    """
    遍历指定路径，返回一个带路径前缀的展平文件列表。

    参数:
        paths (str or list): 要遍历的路径，支持字符串或路径列表。
        suffixes (list): 允许的文件后缀名列表，如 [".txt", ".csv"]，默认 None 表示不限制。
        absolute (bool): 是否返回绝对路径，默认 True。

    返回:
        list: 带路径前缀的展平文件列表。
    """
    result = []

    if isinstance(paths, str):
        paths = [paths]

    for path in paths:
        abs_base = os.path.abspath(path)

        for root, _, files in os.walk(path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if suffixes is None or ext in suffixes:
                    full_path = os.path.join(root, file)
                    if absolute:
                        result.append(full_path)
                    else:
                        rel_path = os.path.relpath(full_path, start=abs_base)
                        result.append((abs_base, rel_path))
    return result


def list_files_with_follow(fds):
    if isinstance(fds, dict):
        fds = [fds]
    files_dict = []
    for fd in fds:
        path, *suffixes = fd['main']
        main_file_list = list_files(path, suffixes=suffixes, absolute=False)
        for _, main_file in main_file_list:
            file_dict = [os.path.join(path, main_file)]
            for follow in fd.get('follows', []):
                follow_dir = follow[0]
                follow_file_path_add = None
                for suffix in follow[1:]:
                    main_file_without_suffix = os.path.join(os.path.dirname(main_file), os.path.splitext(os.path.basename(main_file))[0])
                    follow_file_path = os.path.join(follow_dir, f'{main_file_without_suffix}{suffix}')
                    if os.path.exists(follow_file_path):
                        follow_file_path_add = follow_file_path
                        break
                file_dict.append(follow_file_path_add)
            files_dict.append(file_dict)
    return files_dict


if __name__ == '__main__':
    # file_paths = list_files([r'S:\videos\tennis_train_data\detect\train',
    #                          r'D:\Code\aigc-image-ai\service\video_anysis\v2_20250704\converted_photos'],
    #                         suffixes=['.jpg', '.png'], absolute=True)

    fds = [{'main': [r'S:\videos\tennis_train_data\detect\train', '.jpg', '.png'],
            'follows': [[r'S:\videos\tennis_train_data\detect\train', '.txt']]}]
    data = list_files_with_follow(fds)
    print(data)
