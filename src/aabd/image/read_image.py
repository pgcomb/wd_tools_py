import tempfile

import numpy as np
from PIL import Image
import base64
import requests
from io import BytesIO
import os


def detect_input_format(data):
    """自动检测输入数据的格式类型"""
    if isinstance(data, np.ndarray):
        return 'numpy'
    elif isinstance(data, Image.Image):
        return 'pillow'
    elif isinstance(data, str):
        if data.startswith(('http://', 'https://')):
            return 'url'
        if os.path.exists(data):
            return 'filepath'
        try:
            if data.startswith('data:image/'):
                return 'base64'
            base64.b64decode(data)
            return 'base64'
        except:
            pass
    raise ValueError(f"无法识别的输入格式: {data}")


def convert_image(data, output_format, **kwargs):
    """
    自动识别输入格式并转换为指定输出格式。

    参数:
        data: 输入图像数据（支持 numpy, pillow, base64, url, filepath）。
        output_format (str): 指定输出格式，可选值为 'numpy', 'pillow', 'base64', 'url', 'filepath'。
        **kwargs: 可选参数，如 format（图像格式）、save_path（保存路径）等。

    返回:
        转换后的图像数据。
    """
    input_format = detect_input_format(data)
    return _convert_image(data, input_format, output_format, **kwargs)


def _convert_image(data, input_format, output_format, **kwargs):
    """原始转换逻辑（内部使用）"""
    pil_image = _to_pil_image(data, input_format)
    return _from_pil_image(pil_image, output_format, **kwargs)


def _to_pil_image(data, input_format):
    """将输入数据转换为 PIL 图像"""
    if input_format == 'pillow':
        return data.copy()
    elif input_format == 'numpy':
        return Image.fromarray(data)
    elif input_format == 'base64':
        try:
            img_data = base64.b64decode(data)
        except:
            raise ValueError("无效的 Base64 字符串")
        return Image.open(BytesIO(img_data))
    elif input_format == 'url':
        try:
            response = requests.get(data)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except requests.RequestException as e:
            raise ValueError(f"无法从 URL 加载图像: {e}")
    elif input_format == 'filepath':
        return Image.open(data)
    else:
        raise ValueError(f"不支持的输入格式: {input_format}")


def _from_pil_image(pil_image, output_format, **kwargs):
    """将 PIL 图像转换为指定输出格式"""
    if output_format == 'pillow':
        return pil_image
    elif output_format == 'numpy':
        return np.array(pil_image)
    elif output_format == 'base64':
        img_format = kwargs.get('format', 'PNG')
        buffered = BytesIO()
        pil_image.save(buffered, format=img_format)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    elif output_format == 'url':
        img_format = kwargs.get('format', 'PNG')
        buffered = BytesIO()
        pil_image.save(buffered, format=img_format)
        base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return f"data:image/{img_format.lower()};base64,{base64_str}"
    elif output_format == 'filepath':
        save_path = kwargs.get('save_path')
        img_format = kwargs.get('format', 'PNG')
        ext = f".{img_format.lower()}"
        if save_path:
            if not save_path.endswith(ext):
                save_path = os.path.splitext(save_path)[0] + ext
            pil_image.save(save_path, format=img_format)
            return save_path
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                pil_image.save(tmp_file, format=img_format)
                return tmp_file.name
    else:
        raise ValueError(f"不支持的输出格式: {output_format}")


def to_base64(image, fm='PNG'):
    return convert_image(image, 'base64', format=fm)


def to_np(image):
    return convert_image(image, 'numpy')


def to_pil(image):
    return convert_image(image, 'pillow')


def to_file(image, path: str):
    return convert_image(image, 'filepath', save_path=path)
