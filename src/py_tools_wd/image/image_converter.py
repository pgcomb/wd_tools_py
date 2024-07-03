import base64
import io

from PIL import Image as ImageUtil
import numpy as np
from PIL.Image import Image as PIL_Image

NPRgb = np.ndarray
NPImage = np.ndarray
Mask = np.ndarray
MaskImage = np.ndarray
FilePath = str
Base64Image = str
ImageFormat = str


def remove_base64_header(base64_string):
    if base64_string.startswith("data:image"):
        # 寻找逗号的位置，逗号后面就是base64编码的数据部分
        header_end = base64_string.find(",")
        if header_end != -1:
            return base64_string[header_end + 1:]
    return base64_string


def np_split(image: NPImage) -> (NPRgb, Mask):
    mask = None
    if (len(image.shape)) == 2:
        image = np.stack((image, image, image), axis=-1)
    elif len(image.shape) == 3:
        if image.shape[2] == 4:
            image = image[:, :, :3]
            mask = image[:, :, 3]
    return image, mask


def np_merge(image: NPImage, mask: Mask) -> NPImage:
    if (len(image.shape)) == 2:
        if mask is None:
            image = np.stack((image, image, image), axis=-1)
        else:
            image = np.stack((image, image, image, mask), axis=-1)
    elif len(image.shape) == 3:
        if mask is not None:
            if image.shape[2] == 3:
                rgba_image = np.zeros((image.shape[0], image.shape[1], 4), dtype=np.uint8)
                rgba_image[:, :, :3] = image
                rgba_image[:, :, 3] = mask
                image = rgba_image
            elif image.shape[2] == 4:
                image[:, :, 3] = mask
    return image


def pil_to_np(image: PIL_Image) -> (NPRgb, Mask, ImageFormat):
    if image.mode == 'RGBA':
        rgba = np.array(image)
        return rgba[:, :, :3], rgba[:, :, 3], image.format
    elif image.mode == 'RGB':
        return np.array(image), None, image.format
    else:
        image = image.convert('RGB')
        return np.array(image), None, image.format


def np_to_pil(image: NPImage, mask: Mask = None) -> PIL_Image:
    return ImageUtil.fromarray(np_merge(image, mask))


def pil_to_base64(image: PIL_Image) -> Base64Image:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue())
    return img_str.decode('utf-8')


def base64_to_pil(image: Base64Image) -> PIL_Image:
    image = remove_base64_header(image)
    image = base64.b64decode(image)
    image = io.BytesIO(image)
    image = ImageUtil.open(image)
    return image


def file_to_pil(image_path: FilePath) -> PIL_Image:
    return ImageUtil.open(image_path)


def pil_to_file(image: PIL_Image, file_path: FilePath):
    image.save(file_path)


def file_to_np(image_path: FilePath) -> (NPRgb, Mask, ImageFormat):
    return pil_to_np(file_to_pil(image_path))


def np_to_file(image: NPImage, file_path: FilePath, mask: Mask = None):
    pil_to_file(np_to_pil(image, mask), file_path)


def file_to_base64(image_path: FilePath) -> Base64Image:
    return pil_to_base64(file_to_pil(image_path))


def np_to_base64(image: NPImage, mask: Mask = None) -> str:
    image = np_to_pil(image, mask)
    return pil_to_base64(image)


def base64_to_np(image: Base64Image) -> (NPRgb, Mask, ImageFormat):
    return pil_to_np(base64_to_pil(image))


def base64_to_file(image: Base64Image, file_path: FilePath):
    pil_to_file(base64_to_pil(image), file_path)


def to_base64(image):
    if isinstance(image, str):
        return file_to_base64(image)
    elif isinstance(image, PIL_Image):
        return pil_to_base64(image)
    elif isinstance(image, NPImage):
        return np_to_base64(image)
    raise Exception('image type error')


def to_np(image):
    if isinstance(image, str):
        try:
            return base64_to_np(image)
        except:
            return file_to_np(image)
    elif isinstance(image, PIL_Image):
        return pil_to_np(image)
    raise Exception('image type error')


def to_pil(image):
    if isinstance(image, str):
        try:
            return base64_to_pil(image)
        except:
            return file_to_pil(image)
    elif isinstance(image, NPImage):
        return np_to_pil(image)
    raise Exception('image type error')


def to_file(image, path: FilePath):
    if isinstance(image, str):
        base64_to_file(image, path)
    elif isinstance(image, PIL_Image):
        pil_to_file(image, path)
    elif isinstance(image, NPImage):
        np_to_file(image, path)
    else:
        raise Exception('image type error')
