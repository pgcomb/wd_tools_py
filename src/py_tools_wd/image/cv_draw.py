import numpy as np
import cv2


def to_font_size(height, thickness=1):
    return round((height - thickness // 2 - 1) / 21, 1)


def draw_rect(image: np.ndarray, box: list | np.ndarray, bg_color=None, outline_color=(255, 0, 0),
              outline_width=1, label_text=None, label_bg_color=(255, 0, 0),
              label_color=(255, 255, 255),  # 新增参数：标签文本颜色，默认白色
              label_size=20,  # 字的高
              box_mode='xyxy', alpha=None):
    """
    在图上画一个框以及附带一个标签(可选)
    :param image: 输入的图像（numpy数组）
    :param box: 框的位置（列表或numpy数组）
    :param bg_color: 框的背景颜色（RGB或RGBA，默认不透明，None则无背景）
    :param outline_color: 框的轮廓颜色（RGB或RGBA，默认蓝色，不透明）
    :param outline_width: 框的轮廓宽度
    :param label_text: 标签文本（None则无标签）
    :param label_bg_color: 标签背景色（RGB或RGBA，默认不透明，None则无背景）
    :param label_color: 标签文本颜色（RGB，默认白色）
    :param label_size: 标签字体大小（默认0.5）
    :param box_mode: 坐标格式（'xyxy'、'xywh'、'cxywh'）
    :param alpha 透明度
    :return: 绘制后的图像（numpy数组）
    """
    if alpha is not None:
        ori_image = image.copy()
    label_size = to_font_size(label_size, 1)

    def process_color(color):
        if color is None:
            return None
        if len(color) == 3:
            return (color[2], color[1], color[0])  # RGB转BGR
        elif len(color) == 4:
            return (color[2], color[1], color[0], color[3])  # RGBA转BGRA
        else:
            raise ValueError("颜色参数必须为RGB或RGBA格式")

    bg_color_bgr = process_color(bg_color)
    outline_color_bgr = process_color(outline_color)
    label_bg_color_bgr = process_color(label_bg_color)
    label_color_bgr = process_color(label_color)  # 处理标签文本颜色

    h, w = image.shape[:2]

    def convert_box_to_xyxy(box, box_mode):
        if box_mode == 'xyxy':
            x1, y1, x2, y2 = box[:4]
        elif box_mode == 'xywh':
            x1, y1, w_box, h_box = box[:4]
            x2 = x1 + w_box
            y2 = y1 + h_box
        elif box_mode == 'cxywh':
            cx, cy, w_box, h_box = box[:4]
            x1 = cx - w_box / 2
            y1 = cy - h_box / 2
            x2 = cx + w_box / 2
            y2 = cy + h_box / 2
        else:
            raise ValueError("无效的box_mode")

        if all(v < 1.0 for v in [x1, y1, x2, y2]):
            x1 *= w
            y1 *= h
            x2 *= w
            y2 *= h

        return (int(x1), int(y1), int(x2), int(y2))

    x1, y1, x2, y2 = convert_box_to_xyxy(box, box_mode)
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w - 1, x2)
    y2 = min(h - 1, y2)

    if bg_color is not None:
        cv2.rectangle(image, (x1, y1), (x2, y2), bg_color_bgr[:3], -1)

    cv2.rectangle(image, (x1, y1), (x2, y2), outline_color_bgr[:3], outline_width)

    if label_text is not None:
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height), baseline = cv2.getTextSize(label_text, font, label_size, 1)

        label_x1 = x1
        label_y1 = y1 - text_height - baseline
        label_x2 = x1 + text_width
        label_y2 = y1

        if label_y1 < 0:
            label_y1 = y1
            label_y2 = y1 + text_height + baseline

        label_x1 = max(0, label_x1)
        label_x2 = min(w, label_x2)

        if label_bg_color is not None:
            cv2.rectangle(image, (label_x1, label_y1), (label_x2, label_y2), label_bg_color_bgr[:3], -1)

        text_y = label_y2 - baseline
        cv2.putText(image, label_text, (label_x1, text_y), font, label_size, label_color_bgr[:3], 1)

    if alpha is not None:
        image = (1 - alpha) * ori_image + alpha * image
        image = image.astype(np.uint8)
    return image


def draw_circle(image: np.ndarray, circle: list | np.ndarray, bg_color=None, outline_color=None, outline_width=1,
                label_text=None, label_bg_color=None, label_color=None, label_size=20, circle_mode='xyxy', alpha=None):
    """
    在图像上绘制一个圆及可选标签
    :param image: 输入图像（numpy数组）
    :param circle: 圆的参数（根据circle_mode不同，格式不同）
    :param bg_color: 圆的填充颜色（RGB，默认不透明，None则无填充）
    :param outline_color: 圆的轮廓颜色（RGB，默认不透明，None则无轮廓）
    :param outline_width: 轮廓线宽（默认1）
    :param label_text: 标签文本（None则无标签）
    :param label_bg_color: 标签背景色（RGB，默认不透明，None则无背景）
    :param label_color: 标签文本颜色（RGB，默认白色）
    :param label_size: 标签字体大小（默认0.5）
    :param circle_mode: 坐标格式：
        - 'xyxy'：左上右下坐标
        - 'xywh'：左上坐标+宽高
        - 'cxywh'：中心坐标+宽高（半径取宽高的最小值的一半）
        - 'cxyr'：中心坐标+半径（直接指定半径）
    :param alpha 透明度
    :return: 绘制后的图像
    """

    if outline_color is None and bg_color is None:
        outline_color = (255, 0, 0)
    if label_text is not None and label_color is None and label_bg_color is None:
        label_color = (255, 255, 255)
        label_bg_color = (255, 0, 0)
    if alpha is not None:
        ori_image = image.copy()

    def process_color(color):
        """处理颜色参数（RGB转BGR）"""
        if color is None:
            return None
        if len(color) == 3:
            return (color[2], color[1], color[0])  # RGB转BGR
        elif len(color) == 4:
            return (color[2], color[1], color[0], color[3])  # RGBA转BGRA
        else:
            raise ValueError("颜色参数必须为RGB或RGBA格式")

    # 颜色处理
    bg_color_bgr = process_color(bg_color)
    outline_color_bgr = process_color(outline_color)
    label_bg_color_bgr = process_color(label_bg_color)
    label_color_bgr = process_color(label_color) if label_color else (255, 255, 255)  # 默认白色

    h, w = image.shape[:2]

    # 坐标转换函数
    def convert_circle_params(circle, mode):
        if mode == 'cxyr':
            # 中心坐标+半径
            x, y, r = circle[:3]
            # 处理归一化坐标
            if all(v < 1.0 for v in [x, y, r]):
                x *= w
                y *= h
                r *= w  # 半径按宽度归一化
            return (int(x), int(y)), int(r)
        elif mode == 'cxywh':
            # 中心坐标+宽高（半径取宽高的最小值的一半）
            x_center, y_center, w_box, h_box = circle[:4]
            if all(v < 1.0 for v in [x_center, y_center, w_box, h_box]):
                x_center *= w
                y_center *= h
                w_box *= w
                h_box *= h
            r = min(w_box, h_box) // 2  # 半径取较小边的一半
            return (int(x_center), int(y_center)), int(r)
        elif mode == 'xyxy':
            # 左上右下坐标 → 转换为中心坐标+半径
            x1, y1, x2, y2 = circle[:4]
            if all(v < 1.0 for v in [x1, y1, x2, y2]):
                x1 *= w
                y1 *= h
                x2 *= w
                y2 *= h
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            width = x2 - x1
            height = y2 - y1
            r = min(width, height) // 2
            return (int(center_x), int(center_y)), int(r)
        elif mode == 'xywh':
            # 左上坐标+宽高 → 转换为中心坐标+半径
            x, y, w_box, h_box = circle[:4]
            if all(v < 1.0 for v in [x, y, w_box, h_box]):
                x *= w
                y *= h
                w_box *= w
                h_box *= h
            center_x = x + w_box // 2
            center_y = y + h_box // 2
            r = min(w_box, h_box) // 2
            return (int(center_x), int(center_y)), int(r)
        else:
            raise ValueError(f"无效的circle_mode: {mode}")

    # 获取中心和半径
    center, radius = convert_circle_params(circle, circle_mode)

    # 绘制填充圆
    if bg_color is not None:
        cv2.circle(image, center, radius, bg_color_bgr[:3], -1)

    # 绘制轮廓
    if outline_color is not None and outline_width > 0:
        cv2.circle(image, center, radius, outline_color_bgr[:3], outline_width)

    # 处理标签
    if label_text is not None:
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height), baseline = cv2.getTextSize(label_text, font, to_font_size(label_size, 1), 1)

        # 标签位置计算（默认在圆上方）
        label_x_center = center[0]
        label_y_center = center[1] - radius - text_height - baseline
        label_x1 = label_x_center - text_width // 2
        label_y1 = label_y_center
        label_x2 = label_x_center + text_width // 2
        label_y2 = label_y_center + text_height + baseline

        # 调整位置
        if label_y1 < 0:
            # 如果超出上边界，放到圆下方
            label_y_center = center[1] + radius
            label_y1 = label_y_center
            label_y2 = label_y_center + text_height + baseline

        # 边界检查
        label_x1 = max(0, label_x1)
        label_x2 = min(w, label_x2)
        label_y1 = max(0, label_y1)
        label_y2 = min(h, label_y2)

        # 绘制标签背景
        if label_bg_color is not None:
            cv2.rectangle(image, (label_x1, label_y1), (label_x2, label_y2), label_bg_color_bgr[:3], -1)

        # 绘制文本
        text_x = label_x_center - text_width // 2
        text_y = label_y2 - baseline
        cv2.putText(image, label_text, (text_x, text_y), font, to_font_size(label_size, 1), label_color_bgr[:3], 1)
    if alpha is not None:
        image = (1 - alpha) * ori_image + alpha * image
        image = image.astype(np.uint8)
    return image


def draw_polyline(image, segments, color=(0, 255, 0), thickness=2, alpha=None):
    """
    在图像上绘制多段线

    参数:
        image (numpy.ndarray): 输入图像（NumPy数组）
        segments (list): 线段列表，格式为 [[[x1,y1],[x2,y2]], [[x3,y3],[x4,y4]], ...]
        color (tuple): BGR颜色格式（默认绿色）
        thickness (int): 线条粗细（默认2像素）
        param alpha 透明度
    返回:
        numpy.ndarray: 绘制后的图像
    """
    if alpha is not None:
        ori_image = image.copy()
    for segment in segments:
        # 检查线段是否有效（包含两个点）
        if len(segment) != 2:
            continue  # 跳过无效线段

        # 获取线段的两个端点
        pt1 = (int(segment[0][0]), int(segment[0][1]))
        pt2 = (int(segment[1][0]), int(segment[1][1]))

        # 绘制线段
        cv2.line(image, pt1, pt2, color, thickness)
    if alpha is not None:
        image = (1 - alpha) * ori_image + alpha * image
        image = image.astype(np.uint8)
    return image


def add_multiline_text_to_image(
        img: np.ndarray,
        text,
        font_color=(255, 255, 255),
        font_size=15,
        bg_color=(0, 0, 0),
        font_face=cv2.FONT_HERSHEY_SIMPLEX,
        thickness=1,
        x_offset=10,
        y_offset=20,
        line_spacing=1, alpha=None
):
    """
    在图像左上角绘制多行文字

    参数:
    img: 输入的numpy图像数组
    text: 字符串（用换行分割）或字符串列表
    font_color: 字体颜色 (BGR格式)
    font_size: 字体高度（像素）
    bg_color: 背景颜色 (BGR格式)
    font_face: OpenCV字体类型
    thickness: 字体粗细
    x_offset: 左边距
    y_offset: 上边距
    line_spacing: 行间距
    param alpha 透明度
    """
    if alpha is not None:
        ori_image = image.copy()
    # 将输入文本转换为列表
    if isinstance(text, str):
        lines = text.split('\n')
    else:
        lines = list(text)

    # 计算字体缩放比例

    scale = to_font_size(font_size, thickness)

    current_y = y_offset  # 初始y坐标

    for line in lines:
        # 获取当前行的文字尺寸
        (text_width, text_height), _ = cv2.getTextSize(line, font_face, scale, thickness)

        # 确保current_y至少为文字高度
        if current_y < text_height:
            current_y = text_height

        # 计算矩形区域坐标
        rect_top_left = (x_offset, current_y - text_height)
        rect_bottom_right = (x_offset + text_width, current_y)

        # 绘制背景矩形
        cv2.rectangle(img, rect_top_left, rect_bottom_right, bg_color, -1)

        # 绘制文字
        cv2.putText(
            img,
            line,
            (x_offset, current_y),
            font_face,
            scale,
            font_color,
            thickness,
            lineType=cv2.LINE_AA
        )

        # 更新current_y到下一行位置
        current_y += (text_height + line_spacing)
    if alpha is not None:
        img = (1 - alpha) * ori_image + alpha * img
        img = img.astype(np.uint8)
    return img


if __name__ == '__main__':
    import cv2

    image = cv2.imread(r'D:\codes\projects\python240409\tennis\1.jpg')
    image = draw_rect(image, box=[200, 200, 500, 500], alpha=0.5, label_text='222')
    image = draw_circle(image, circle=[200, 200, 500, 500],bg_color=(255,0,0), alpha=0.5, label_text='111')
    image = draw_polyline(image, segments=[[[0, 0], [200, 200]],[[200,200],[500,200]]],alpha=0.5)
    image = add_multiline_text_to_image(image,text='111\n2343',alpha=0.5)
    cv2.imshow('image', image)
    cv2.waitKey(0)
