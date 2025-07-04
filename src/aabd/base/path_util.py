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

