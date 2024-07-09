import numpy as np


def xywh2xyxy(xywh):
    if len(xywh) == 0:
        return xywh

    if isinstance(xywh, dict):
        return {'x1': xywh[0], 'y1': xywh[1], 'x2': xywh[0] + xywh[2], 'y2': xywh[1] + xywh[3]}
    data_list = []

    if isinstance(xywh[0], list):
        for _xywh in xywh:
            data_list.append([_xywh[0], _xywh[1], _xywh[0] + _xywh[2], _xywh[1] + _xywh[3]])
    elif isinstance(xywh[0], np.ndarray):
        for _xywh in xywh:
            data_list.append(np.array([_xywh[0], _xywh[1], _xywh[0] + _xywh[2], _xywh[1] + _xywh[3]]))
    elif isinstance(xywh[0], tuple):
        for _xywh in xywh:
            data_list.append((_xywh[0], _xywh[1], _xywh[0] + _xywh[2], _xywh[1] + _xywh[3]))
    elif isinstance(xywh[0], dict):
        for _xywh in xywh:
            data_list.append({'x1': _xywh[0], 'y1': _xywh[1], 'x2': _xywh[0] + _xywh[2], 'y2': _xywh[1] + _xywh[3]})
    else:
        data_list = [xywh[0], xywh[1], xywh[0] + xywh[2], xywh[1] + xywh[3]]
    if isinstance(xywh, list):
        return data_list
    elif isinstance(xywh, np.ndarray):
        return np.array(data_list)
    elif isinstance(xywh, tuple):
        return tuple(data_list)


def xywh2xyxy_list(xywh):
    xyxy = xywh2xyxy(xywh)
    data_list = []
    for _xyxy_ in xyxy:
        if isinstance(_xyxy_, np.ndarray) or isinstance(_xyxy_, list) or isinstance(_xyxy_, tuple):
            data_ele = []
            for xy2 in _xyxy_:
                if 'int' in str(type(xy2)):
                    data_ele.append(int(xy2))
                elif 'float' in str(type(xy2)):
                    data_ele.append(float(xy2))
            data_list.append(data_ele)
        else:
            if 'int' in str(type(_xyxy_)):
                data_list.append(int(_xyxy_))
            elif 'float' in str(type(_xyxy_)):
                data_list.append(float(_xyxy_))
    return data_list


def xywh2xyxy_np(xywh):
    return np.array(xywh2xyxy_list(xywh))


def xyxy2xywh(xyxy):
    if len(xyxy) == 0:
        return xyxy

    if isinstance(xyxy, dict):
        return {'x': xyxy[0], 'y': xyxy[1], 'w': xyxy[2] - xyxy[0], 'h': xyxy[3] - xyxy[1]}
    data_list = []

    if isinstance(xyxy[0], list):
        for _xyxy in xyxy:
            data_list.append([_xyxy[0], _xyxy[1], _xyxy[2] - _xyxy[0], _xyxy[3] - _xyxy[1]])
    elif isinstance(xyxy[0], np.ndarray):
        for _xyxy in xyxy:
            data_list.append(np.array([_xyxy[0], _xyxy[1], _xyxy[2] - _xyxy[0], _xyxy[3] - _xyxy[1]]))
    elif isinstance(xyxy[0], tuple):
        for _xyxy in xyxy:
            data_list.append((_xyxy[0], _xyxy[1], _xyxy[2] - _xyxy[0], _xyxy[3] - _xyxy[1]))
    elif isinstance(xyxy[0], dict):
        for _xyxy in xyxy:
            data_list.append({'x': _xyxy[0], 'y': _xyxy[1], 'w': _xyxy[2] - _xyxy[0], 'h': _xyxy[3] - _xyxy[1]})
    else:
        data_list = [xyxy[0], xyxy[1], xyxy[2] - xyxy[0], xyxy[3] - xyxy[1]]
    if isinstance(xyxy, list):
        return data_list
    elif isinstance(xyxy, np.ndarray):
        return np.array(data_list)
    elif isinstance(xyxy, tuple):
        return tuple(data_list)


def xyxy2xywh_list(xyxy):
    xywh = xyxy2xywh(xyxy)
    data_list = []
    for _xywh_ in xywh:
        if isinstance(_xywh_, np.ndarray) or isinstance(_xywh_, list) or isinstance(_xywh_, tuple):
            data_ele = []
            for xy2 in _xywh_:
                if 'int' in str(type(xy2)):
                    data_ele.append(int(xy2))
                elif 'float' in str(type(xy2)):
                    data_ele.append(float(xy2))
            data_list.append(data_ele)
        else:
            if 'int' in str(type(_xywh_)):
                data_list.append(int(_xywh_))
            elif 'float' in str(type(_xywh_)):
                data_list.append(float(_xywh_))
    return data_list


def xyxy2xywh_np(xyxy):
    return np.array(xyxy2xywh_list(xyxy))


def bbox_iou(box1, box2):
    b1_x1, b1_y1, b1_x2, b1_y2 = box1
    b2_x1, b2_y1, b2_x2, b2_y2 = box2

    inter_x1 = max(b1_x1, b2_x1)
    inter_y1 = max(b1_y1, b2_y1)
    inter_x2 = min(b1_x2, b2_x2)
    inter_y2 = min(b1_y2, b2_y2)

    if inter_x2 < inter_x1 or inter_y2 < inter_y1:
        return 0.0

    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)

    area_box1 = (b1_x2 - b1_x1) * (b1_y2 - b1_y1)
    area_box2 = (b2_x2 - b2_x1) * (b2_y2 - b2_y1)

    union_area = area_box1 + area_box2 - inter_area

    iou = inter_area / union_area

    return iou
