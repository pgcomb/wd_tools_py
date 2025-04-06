import os
import shutil
import random
import argparse


def random_extract_files_by_ratio(src_dir, target_dir, number, src_file_suffix=None, options='copy',
                                  follow_src_dir=None, follow_file_suffix='.txt',
                                  keep_tree=True, follow_target_dir=None, no_tree_dir_size=-1, seed=None):
    """
    从一个文件夹提取文件
    :param src_dir: 文件路径
    :param target_dir: 目标路径
    :param number: 比例或数量 小于等于1为比例  大于1为数量
    :param src_file_suffix: 原始文件类型 jpg png webp jpeg bmp
    :param options: copy 或 move
    :param follow_src_dir: 跟随的文件路径
    :param follow_file_suffix: 跟随的文件格式
    :param follow_target_dir: 跟随的文件输出路径
    :param keep_tree: True 保持文件夹结构 False 平铺
    :param no_tree_dir_size: keep_tree=False 时 可以设置一个值输出的文件每多少个放一个文件夹
    :param seed: 随机种子（整数），用于保证随机抽取的可重复性

    :return:
    """

    # 参数验证
    if follow_src_dir is not None and follow_target_dir is None:
        follow_target_dir = target_dir

    if not os.path.exists(src_dir):
        raise NotADirectoryError(f"Source directory {src_dir} does not exist.")
    if src_file_suffix is not None and not isinstance(src_file_suffix, (str, list)):
        raise TypeError("src_file_suffix must be a string or list of strings")

    if seed is not None and not isinstance(seed, int):
        raise TypeError("seed must be an integer or None")
    # 创建目标目录（如果不存在）
    os.makedirs(target_dir, exist_ok=True)
    if follow_src_dir:
        os.makedirs(follow_target_dir, exist_ok=True)

    # 收集符合条件的文件
    file_list = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            # 判断文件后缀是否匹配
            if src_file_suffix is None:
                file_list.append(os.path.join(root, file))
            else:
                if isinstance(src_file_suffix, str):
                    if file.endswith(src_file_suffix):
                        file_list.append(os.path.join(root, file))
                else:  # 列表类型
                    for suffix in src_file_suffix:
                        if file.endswith(suffix):
                            file_list.append(os.path.join(root, file))
                            break  # 避免重复添加
    total_files = len(file_list)
    if total_files == 0:
        print("No files found in source directory.")
        return

    # 计算要抽取的数量
    if number <= 1:
        num_to_copy = max(1, int(total_files * number))  # 至少一个文件
    else:
        num_to_copy = int(number)
    num_to_copy = min(num_to_copy, total_files)

    # 设置随机种子并抽取文件
    prev_state = None
    if seed is not None:
        # 保存当前随机状态
        prev_state = random.getstate()
        random.seed(seed)

    try:
        selected_files = random.sample(file_list, num_to_copy)
    finally:
        # 恢复之前的随机状态（如果设置了种子）
        if seed is not None and prev_state is not None:
            random.setstate(prev_state)
    # 处理每个文件
    for idx, src_file in enumerate(selected_files):
        # 处理主文件
        relative_path = os.path.relpath(src_file, src_dir)
        base_name = os.path.basename(src_file)

        # 主文件的目标路径构建
        if keep_tree:
            target_subdir = os.path.dirname(relative_path)
            target_dir_path = os.path.join(target_dir, target_subdir)
        else:
            if no_tree_dir_size != -1:
                group = idx // no_tree_dir_size
                target_subdir = str(group)
            else:
                target_subdir = ""
            target_dir_path = os.path.join(target_dir, target_subdir)

        target_file_path = os.path.join(target_dir_path, base_name)
        # 创建目标目录
        os.makedirs(target_dir_path, exist_ok=True)

        # 执行复制或移动操作
        if options == 'copy':
            shutil.copy2(src_file, target_file_path)
        elif options == 'move':
            shutil.move(src_file, target_file_path)
        else:
            raise ValueError("options must be 'copy' or 'move'")

        # 处理跟随文件
        if follow_src_dir:
            # 构造跟随文件的源路径
            follow_file_name = f"{os.path.splitext(base_name)[0]}{follow_file_suffix}"
            follow_src_subdir = os.path.dirname(relative_path)
            follow_src_path = os.path.join(follow_src_dir, follow_src_subdir, follow_file_name)

            if not os.path.exists(follow_src_path):
                print(f"Warning: Follow file {follow_src_path} not found.")
                continue  # 跳过不存在的跟随文件

            # 构造跟随文件的目标路径
            if keep_tree:
                follow_target_subdir = follow_src_subdir
            else:
                if no_tree_dir_size != -1:
                    group = idx // no_tree_dir_size
                    follow_target_subdir = str(group)
                else:
                    follow_target_subdir = ""
            follow_target_dir_path = os.path.join(follow_target_dir, follow_target_subdir)

            follow_target_file_path = os.path.join(follow_target_dir_path, follow_file_name)
            os.makedirs(follow_target_dir_path, exist_ok=True)

            # 执行跟随文件操作
            if options == 'copy':
                shutil.copy2(follow_src_path, follow_target_file_path)
            else:
                shutil.move(follow_src_path, follow_target_file_path)

    print(f"Successfully extracted {num_to_copy} files.")


def main():
    parser = argparse.ArgumentParser(description='文件随机提取工具')

    # 必填参数
    parser.add_argument('target_dir', type=str, help='目标文件夹路径')
    parser.add_argument('number', type=float, help='提取比例（≤1）或数量（>1）')

    # 可选参数
    parser.add_argument('--src_dir', type=str, default=os.getcwd(),
                        help='源文件夹路径（默认当前目录）')
    parser.add_argument('--src_file_suffix', type=str,
                        help='源文件后缀（多个用逗号分隔，如 ".jpg,.png"）')
    parser.add_argument('--options', choices=['copy', 'move'], default='copy',
                        help='操作类型（默认copy）')
    parser.add_argument('--follow_src_dir', type=str,
                        help='需要跟随处理的源文件夹路径')
    parser.add_argument('--follow_file_suffix', type=str, default='.txt',
                        help='跟随文件后缀（默认.txt）')
    parser.add_argument('--keep_tree', action='store_true', default=True,
                        help='是否保留源目录结构（默认保留）')
    parser.add_argument('--no_tree_dir_size', type=int, default=-1,
                        help='不保留目录时每组文件数量（默认不分组）')
    parser.add_argument('--seed', type=int, default=None,
                        help='随机种子（整数，用于结果复现）')

    args = parser.parse_args()

    # 处理跟随文件的目标路径
    if args.follow_src_dir and not args.follow_target_dir:
        args.follow_target_dir = args.target_dir

    # 处理文件后缀格式
    if args.src_file_suffix:
        args.src_file_suffix = [s.strip() for s in args.src_file_suffix.split(',')]

    # 调用核心函数
    random_extract_files_by_ratio(
        src_dir=args.src_dir,
        target_dir=args.target_dir,
        number=args.number,
        src_file_suffix=args.src_file_suffix,
        options=args.options,
        follow_src_dir=args.follow_src_dir,
        follow_file_suffix=args.follow_file_suffix,
        keep_tree=args.keep_tree,
        follow_target_dir=args.follow_target_dir,
        no_tree_dir_size=args.no_tree_dir_size,
        seed=args.seed
    )


if __name__ == '__main__':
    main()
#
# random_extract_files_by_ratio(
#     src_dir="/data/wdxdev/projects/wd_tools_py/src/py_tools_wd/base/src",
#     follow_src_dir="/data/wdxdev/projects/wd_tools_py/src/py_tools_wd/base/src",
#     target_dir="/data/wdxdev/projects/wd_tools_py/src/py_tools_wd/base/target",
#     number=0.5,
#     src_file_suffix=[".jpg"],
#     options='copy',
#     keep_tree=False, no_tree_dir_size=2,seed=123,
# )
