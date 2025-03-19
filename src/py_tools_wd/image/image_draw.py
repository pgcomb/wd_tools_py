import numpy
from PIL import ImageDraw, ImageFont, Image
from importlib.resources import files


def get_font(name, size):
    return ImageFont.truetype(name, size)


def text_box(text, font):
    left, top, right, bottom = font.getbbox(text)
    return right - left, bottom - top


def paste_text(image: Image, xy, text, font, font_color=(255, 0, 0, 255), anchor='lt'):
    if isinstance(font, int):
        font_path = files("py_tools_wd.image").joinpath("AlibabaPuHuiTi-3-65-Medium.ttf").as_posix()
        font = get_font(font_path, font)
    x, y = xy
    text_w, text_h = text_box(text=text, font=font)

    if anchor == 'lc':
        y = int(y - text_h / 2)
        anchor = 'lt'
    elif anchor == 'mc':
        y = int(y - text_h / 2)
        anchor = 'mt'
    elif anchor == 'rc':
        y = int(y - text_h / 2)
        anchor = 'rt'
    draw = ImageDraw.Draw(image)

    if len(font_color) == 4 and font_color[3] < 255:
        image = image.convert('RGBA')
        text_overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
        image_draw = ImageDraw.Draw(text_overlay)
        image_draw.text(xy=(x, y), text=text, font=font, fill=font_color, anchor=anchor)
        image = Image.alpha_composite(image, text_overlay)
        image = image.convert('RGB')
    else:
        draw.text(xy=(x, y), fill=font_color, font=font, text=text, anchor=anchor)
    return image, (x, y, x + text_w, y + text_h)


default_font = get_font('AlibabaPuHuiTi-3-65-Medium.ttf', 10)


def paste_box(image: Image, xyxy, bg_color=None, outline_color=None, outline_width=1, label_text=None,
              label_text_font=default_font, mode='xyxy'):
    if mode == 'cxywh':
        cx, cy, w, h = xyxy
        x1, y1 = int(cx - w / 2), int(cy - h / 2)
        x2, y2 = x1 + w, y1 + h
        xyxy = (x1, y1, x2, y2)
    elif mode == 'xywh':
        x, y, w, h = xyxy
        xyxy = (x, y, x + w, y + h)
    if bg_color is not None:
        image = image.convert('RGBA')
        text_overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
        image_draw = ImageDraw.Draw(text_overlay)
        image_draw.rectangle(xy=xyxy, fill=bg_color)
        image = Image.alpha_composite(image, text_overlay)
        image = image.convert('RGB')
    draw = ImageDraw.Draw(image)
    if outline_color is not None and outline_width is not None:
        draw.rectangle(xy=xyxy, outline=outline_color, width=outline_width)
    if label_text is not None and label_text_font is not None:
        box_x1, box_y1, box_x2, box_y2 = xyxy
        text_w, text_h = text_box(label_text, label_text_font)
        label_box_x1, label_box_y1, label_box_x2, label_box_y2 = box_x1, box_y1 - text_h - 1, box_x1 + text_w, box_y1 - 1
        image = paste_box(image, xyxy=(label_box_x1, label_box_y1, label_box_x2, label_box_y2), bg_color=(255, 0, 0))
        paste_text(image, xy=(box_x1, box_y1), text=label_text, font_color=(255, 255, 255), font=label_text_font,
                   anchor='lb')
    return image


def paste_image(image: Image, xy, wh, img: Image, alpha_coefficient=1.):
    image = image.convert('RGBA')
    if wh is not None:
        img = img.resize(wh)
    img = img.convert('RGBA')
    if alpha_coefficient != 1.:
        img_np = numpy.array(img)
        img_np[:, :, 3] = img_np[:, :, 3] * alpha_coefficient
        img = Image.fromarray(img_np.astype('uint8'))
    overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
    overlay.paste(img, box=xy)
    image = Image.alpha_composite(image, overlay)
    image = image.convert('RGB')
    return image
