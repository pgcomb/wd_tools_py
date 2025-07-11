import math

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from importlib.resources import files

font_map = {}


def get_font(size):
    font = font_map.get(size)
    if font is None:
        font_path = files("aabd.image").joinpath("AlibabaPuHuiTi-3-65-Medium.ttf").as_posix()
        font = ImageFont.truetype(font_path, size)
    return font


def draw_rect(image: Image, box: list | np.ndarray, bg_color=None, outline_color=(255, 0, 0),
              outline_width=1, label_text=None, label_bg_color=(255, 0, 0),
              label_color=(255, 255, 255), label_size=20, box_mode='xyxy', alpha: bool | int | float = False):
    """
    在图上画一个框以及附带一个标签(可选)
    :param image: 输入的图像（Pillow图片）
    :param box: 框的位置（列表或numpy数组）
    :param bg_color: 框的背景颜色（(R, G, B) or (R, G, B, A)，None则无背景）
    :param outline_color: 框的轮廓颜色（(R, G, B) or (R, G, B, A)）
    :param outline_width: 框的轮廓宽度
    :param label_text: 标签文本（None则无标签）
    :param label_bg_color: 标签背景色（(R, G, B) or (R, G, B, A)，None则无背景）
    :param label_color: 标签文本颜色（(R, G, B) or (R, G, B, A)，默认白色）
    :param label_size: 标签字体大小（默认20）
    :param box_mode: 坐标格式（'xyxy'、'xywh'、'cxywh'）
    :param alpha: 是否处理透明
    :return: 绘制后的图像（pillow图片）
    """
    if alpha is not None and alpha is not False:
        if not isinstance(alpha, bool):
            if alpha <= 1:
                alpha = int(alpha * 255)
            bg_color = (*bg_color[:3], alpha) if bg_color else bg_color
            outline_color = (*outline_color[:3], alpha) if outline_color else outline_color
            label_bg_color = (*label_bg_color[:3], alpha) if label_bg_color else label_bg_color
            label_color = (*label_color[:3], alpha) if label_color else label_color
        ori_image = image
        image = image.convert("RGBA")
    image_width, image_height = image.size

    draw = ImageDraw.Draw(image)

    # 转换box坐标到xyxy
    if box_mode == 'xyxy':
        x1, y1, x2, y2 = box
    elif box_mode == 'xywh':
        x1, y1, w, h = box
        x2 = x1 + w
        y2 = y1 + h
    elif box_mode == 'cxywh':
        cx, cy, w, h = box
        x1 = cx - w / 2
        y1 = cy - h / 2
        x2 = x1 + w
        y2 = y1 + h
    else:
        raise ValueError(f"Unsupported box mode: {box_mode}")

    # 转换为整数
    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

    # 绘制填充的矩形
    if bg_color is not None:
        draw.rectangle([x1, y1, x2, y2], fill=bg_color)

    # 绘制轮廓
    draw.rectangle([x1, y1, x2, y2], outline=outline_color, width=outline_width)

    # 处理标签
    if label_text is not None:
        font = get_font(label_size)

        tbox_x1, tbox_y1, tbox_x2, tbox_y2 = draw.textbbox((x1, y1), label_text, font=font, anchor='lb')
        if tbox_x2 > image_width:
            offset_x = tbox_x2 - image_width
            tbox_x1 -= offset_x
            tbox_x2 -= offset_x
        if tbox_y1 < 0:
            tbox_y2 = y2 + tbox_y2 - tbox_y1
            tbox_y1 = y2
        if label_bg_color is not None:
            draw.rectangle([tbox_x1, tbox_y1, tbox_x2, tbox_y2], fill=label_bg_color)
        draw.text((tbox_x1, tbox_y2), label_text, font=font, fill=label_color, anchor='lb')

    if alpha is not None and alpha is not False:
        r, g, b, a = image.split()
        return Image.composite(image.convert('RGB'), ori_image, a)
    else:
        return image


def pad_image(img, top=0, bottom=0, left=0, right=0, color=(255, 255, 255)):
    """
    使用 Pillow 在图像四周填充给定像素或比例。

    参数:
        img: 图像路径或 PIL.Image.Image 对象
        top, bottom, left, right: 填充值，小于1表示比例，大于等于1表示像素
        color: 填充颜色 (R, G, G)

    返回:
        填充后的图像 (PIL.Image.Image)
    """

    # 获取图像尺寸
    width, height = img.size

    # 计算填充像素数
    def get_padding(val, dim):
        if val < 1:
            return int(val * dim)
        else:
            return int(val)

    top_pad = get_padding(top, height)
    bottom_pad = get_padding(bottom, height)
    left_pad = get_padding(left, width)
    right_pad = get_padding(right, width)

    # 新图像尺寸
    new_width = width + left_pad + right_pad
    new_height = height + top_pad + bottom_pad

    # 创建新图像并填充颜色
    new_img = Image.new("RGB", (new_width, new_height), color=color)

    # 粘贴原图像到新图像
    new_img.paste(img, (left_pad, top_pad))

    return new_img


def draw_circle(image: Image, circle: list | np.ndarray,
                bg_color=None, outline_color=(255, 0, 0), outline_width=1,
                label_text=None, label_bg_color=(255, 0, 0), label_color=(255, 255, 0), label_size=20,
                circle_mode='xyxy', alpha: bool | int | float = False):
    """
    在图像上绘制一个圆及可选标签
    :param image: 输入图像（Pillow）
    :param circle: 圆的参数（根据circle_mode不同，格式不同）
    :param bg_color: 圆的填充颜色（(R, G, B) or (R, G, B, A)，None则无填充）
    :param outline_color: 圆的轮廓颜色（(R, G, B) or (R, G, B, A)，None则无轮廓）
    :param outline_width: 轮廓线宽（默认1）
    :param label_text: 标签文本（None则无标签）
    :param label_bg_color: 标签背景色（(R, G, B) or (R, G, B, A)，None则无背景）
    :param label_color: 标签文本颜色（(R, G, B) or (R, G, B, A)，默认白色）
    :param label_size: 标签字体大小（默认20）
    :param circle_mode: 坐标格式：
        - 'xyxy'：左上右下坐标
        - 'xywh'：左上坐标+宽高
        - 'cxywh'：中心坐标+宽高（半径取宽高的最小值的一半）
        - 'cxyr'：中心坐标+半径（直接指定半径）
    :param alpha 是否处理透明
    :return: 绘制后的图像
    """
    if alpha is not None and alpha is not False:
        if not isinstance(alpha, bool):
            if alpha <= 1:
                alpha = int(alpha * 255)
            bg_color = (*bg_color[:3], alpha) if bg_color else bg_color
            outline_color = (*outline_color[:3], alpha) if outline_color else outline_color
            label_bg_color = (*label_bg_color[:3], alpha) if label_bg_color else label_bg_color
            label_color = (*label_color[:3], alpha) if label_color else label_color
        ori_image = image
        image = image.convert("RGBA")
    image_width, image_height = image.size

    draw = ImageDraw.Draw(image)

    # 解析圆的参数
    if circle_mode == 'xyxy':
        if len(circle) < 4:
            raise ValueError("circle must have at least 4 elements for 'xyxy' mode")
        x1, y1, x2, y2 = circle[:4]
        width = x2 - x1
        height = y2 - y1
        cx = x1 + width / 2
        cy = y1 + height / 2
        r = min(width, height) / 2
    elif circle_mode == 'xywh':
        if len(circle) < 4:
            raise ValueError("circle must have at least 4 elements for 'xywh' mode")
        x, y, w, h = circle[:4]
        cx = x + w / 2
        cy = y + h / 2
        r = min(w, h) / 2
    elif circle_mode == 'cxywh':
        if len(circle) < 4:
            raise ValueError("circle must have at least 4 elements for 'cxywh' mode")
        cx, cy, w, h = circle[:4]
        r = min(w, h) / 2
    elif circle_mode == 'cxyr':
        if len(circle) < 3:
            raise ValueError("circle must have at least 3 elements for 'cxyr' mode")
        cx, cy, r = circle[:3]
    else:
        raise ValueError(f"Unsupported circle_mode: {circle_mode}")

    # 绘制圆
    left_top_x = cx - r
    left_top_y = cy - r
    right_bottom_x = cx + r
    right_bottom_y = cy + r
    draw.ellipse(
        (left_top_x, left_top_y, right_bottom_x, right_bottom_y),
        fill=bg_color,
        outline=outline_color,
        width=outline_width
    )

    # 绘制标签
    if label_text is not None:
        # 加载字体
        font = get_font(label_size)

        tbox_x1, tbox_y1, tbox_x2, tbox_y2 = draw.textbbox((cx, cy - r), label_text, font=font, anchor='mb')

        if tbox_x2 > image_width:
            offset_x = tbox_x2 - image_width
            tbox_x1 -= offset_x
            tbox_x2 -= offset_x
        if tbox_y1 < 0:
            tbox_y2 = cy + r + tbox_y2 - tbox_y1
            tbox_y1 = cy + r
        if label_bg_color is not None:
            draw.rectangle([tbox_x1, tbox_y1, tbox_x2, tbox_y2], fill=label_bg_color)

        draw.text((tbox_x1, tbox_y2), label_text, font=font, fill=label_color, anchor='lb')

    if alpha is not None and alpha is not False:
        r, g, b, a = image.split()
        return Image.composite(image.convert('RGB'), ori_image, a)
    else:
        return image


def draw_text(image, text, base_point=(0, 0), anchor='ld',
              font_size=20, color=(255, 255, 255), bg_color=(0, 0, 0), alpha: bool | int | float = False):
    """
    在图像上绘制多行文字，支持左上（lt）和左下（lb）对齐。

    :param image: PIL.Image 对象
    :param text: 多行文字，可以是字符串或列表
    :param base_point: 文字区域的基准点 (x, y)
    :param anchor: 对齐方式，'ld' 表示左上对齐，'lb' 表示左下对齐
    :param font_size: 字体大小
    :param color: 文字颜色 (R, G, B) or (R, G, B, A)
    :param bg_color: 文字背景颜色 (R, G, B) or (R, G, B, A)，为 None 则不绘制背景
    :param alpha: 是否处理透明
    :return: 绘制文字后的图像
    """
    if alpha is not None and alpha is not False:
        if not isinstance(alpha, bool):
            if alpha <= 1:
                alpha = int(alpha * 255)
            bg_color = (*bg_color[:3], alpha) if bg_color else bg_color
            color = (*color[:3], alpha) if color else color
        ori_image = image
        image = image.convert("RGBA")
    # 处理输入文本
    if isinstance(text, list):
        text = '\n'.join(text)
    draw = ImageDraw.Draw(image)
    font = get_font(font_size)
    bbox = draw.multiline_textbbox(xy=base_point, text=text, font=font, anchor=anchor)
    if bg_color is not None:
        draw.rectangle(list(bbox), fill=bg_color)
    draw.multiline_text(xy=base_point, text=text, font=font, fill=color, anchor=anchor)

    if alpha is not None and alpha is not False:
        r, g, b, a = image.split()
        return Image.composite(image.convert('RGB'), ori_image, a)
    else:
        return image


def draw_lines(image: Image, lines, color=(255, 0, 0), line_weight=1, alpha: bool | int | float = False):
    """

    :param image: Pillow 图片
    :param lines: 线段集合[[[x11,y11],[x12,y12]],[[x21,y21],[x22,y22]]]
    :param color: 颜色(R, G, B)
    :param line_weight: 线宽
    :param alpha:
    :return:
    """
    if alpha is not None and alpha is not False:
        if not isinstance(alpha, bool):
            if alpha <= 1:
                alpha = int(alpha * 255)
            color = (*color[:3], alpha) if color else color
        ori_image = image
        image = image.convert("RGBA")

    draw = ImageDraw.Draw(image)

    for p1, p2 in lines:
        draw.line([tuple(p1), tuple(p2)], fill=color, width=line_weight)

    if alpha is not None and alpha is not False:
        r, g, b, a = image.split()
        return Image.composite(image.convert('RGB'), ori_image, a)
    else:
        return image


def draw_polyline(image: Image, lines, color=(255, 0, 0), line_weight=1, alpha: bool | int | float = False):
    lines.append([lines[-1][1], lines[0][0]])
    return draw_lines(image, lines, color, line_weight, alpha)


def draw_lines_by_points(image: Image, points, color=(255, 0, 0), line_weight=1, alpha: bool | int | float = False):
    lines = []
    for i in range(len(points) - 1):
        lines.append([points[i], points[i + 1]])
    return draw_lines(image, lines, color, line_weight, alpha)


def draw_polyline_by_points(image: Image, points, color=(255, 0, 0), line_weight=1, alpha: bool | int | float = False):
    lines = []
    for i in range(len(points) - 1):
        lines.append([points[i], points[i + 1]])
    return draw_polyline(image, lines, color, line_weight, alpha)


def _get_points_with_precision(start_point, end_point, precision):
    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    points_in_line = []
    dl = int(math.sqrt(dx ** 2 + dy ** 2) / precision)

    for i in range(dl + 1):
        x = int(start_point[0] + dx / dl * i)
        y = int(start_point[1] + dy / dl * i)
        points_in_line.append((x, y))

    return points_in_line


def draw_gradient_polyline(image, points, start_color=(255, 255, 255), end_color=(64, 144, 254), line_weight=2,
                           precision=None, alpha: int | float = None):
    if precision is None:
        lines_len = 0
        for i in range(len(points) - 1):
            lines_len += math.sqrt((points[i][0] - points[i + 1][0]) ** 2 + (points[i][1] - points[i + 1][1]) ** 2)
        precision = max(lines_len / 20, (len(points) - 1) * 2)
    if alpha is not None:
        if not isinstance(alpha, bool):
            if alpha <= 1:
                alpha = int(alpha * 255)
        ori_image = image
        image = image.convert("RGBA")

    draw = ImageDraw.Draw(image)

    points_list = []
    for i in range(len(points) - 1):
        start_point, end_point = [points[i], points[i + 1]]
        # 使用Bresenham算法或根据精度参数生成更多点
        _points = _get_points_with_precision(start_point, end_point, precision)
        if len(points_list) > 0:  # 如果不是第一条线段，去除重复点
            _points = _points[1:]
        points_list.extend(_points)

    color_diff = [(end_color[i] - start_color[i]) / len(points_list) for i in range(3)]
    accumulated_length = 0
    for i in range(len(points_list) - 1):
        current_color = tuple(int(start_color[j] + (accumulated_length + 1) * color_diff[j]) for j in range(3))
        if alpha is not None:
            current_color += (alpha,)
        draw.line(points_list[i:i + 2], fill=current_color, width=line_weight)
        accumulated_length += 1
    if alpha is not None:
        r, g, b, a = image.split()
        return Image.composite(image.convert('RGB'), ori_image, a)
    else:
        return image


if __name__ == '__main__':
    import time

    image = Image.open(r'D:\Code\aigc-image-ai\http_router\regression_testing\migu\1.jpg')
    start_time = time.time()
    for _ in range(1):
        image = draw_rect(image, [10, 10, 200, 200], label_text='hello', label_size=20, label_color=(255, 255, 0, 100),
                          label_bg_color=(255, 0, 0, 100), bg_color=(255, 255, 0, 100), alpha=0.5)
        image = draw_circle(image, circle=[100, 100, 200, 200], label_text='hello', alpha=0.5)

        image = draw_text(image, 'hello\nworld', (0, 100), 'la')
        image = draw_text(image, 'hello\nworld', (0, 100), 'ld', color=(255, 255, 0, 100), bg_color=(255, 0, 0, 100),
                          alpha=True)
        image = draw_polyline_by_points(image, points=[[300, 100], [250, 100], [250, 200]], line_weight=5, alpha=0.5)
        image = draw_gradient_polyline(image, points=[[300, 300], [300, 0], [200, 300]], line_weight=5)
        image = draw_lines(image, [[[0, 0], [250, 250]], [[250, 300], [0, 200]]], line_weight=5, alpha=0.2)

        image.save('test.png')
    print((time.time() - start_time))
