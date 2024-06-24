import numpy as np
import math


def distance_from_point_to_line(point, line_point1, line_point2):
    # 对于两点坐标为同一点时,返回点与点的距离
    if line_point1 == line_point2:
        point_array = np.array(point)
        point1_array = np.array(line_point1)
        return np.linalg.norm(point_array - point1_array)
    # 计算直线的三个参数
    A = line_point2[1] - line_point1[1]
    B = line_point1[0] - line_point2[0]
    C = (line_point1[1] - line_point2[1]) * line_point1[0] + \
        (line_point2[0] - line_point1[0]) * line_point1[1]
    # 根据点到直线的距离公式计算距离
    distance = np.abs(A * point[0] + B * point[1] + C) / (np.sqrt(A ** 2 + B ** 2))
    if distance == 0:
        distance = 0.00001
    return distance


def cal_distance(p1, p2):
    re = math.sqrt(math.pow((p2[0] - p1[0]), 2) + math.pow((p2[1] - p1[1]), 2))
    if re == 0:
        re = 0.00001
    return re


def cal_k(p1, p2):
    y = p1[0] - p2[0]
    if y == 0:
        y = 0.00001
    return abs((p1[1] - p2[1]) / y)


def pyr_kps(r_kps):
    lm = {"eye_l": {"x": int(r_kps[0][0]), "y": int(r_kps[0][1])},
          "eye_r": {"x": int(r_kps[1][0]), "y": int(r_kps[1][1])},
          "nose": {"x": int(r_kps[2][0]), "y": int(r_kps[2][1])},
          "mouth_l": {"x": int(r_kps[3][0]), "y": int(r_kps[3][1])},
          "mouth_r": {"x": int(r_kps[4][0]), "y": int(r_kps[4][1])}}
    return pyr(lm)


def pyr(landmark):
    eye_l = landmark["eye_l"]
    eye_r = landmark["eye_r"]
    nose = landmark["nose"]
    mouth_l = landmark["mouth_l"]
    mouth_r = landmark["mouth_r"]

    # 两眼中点
    eye_c_x = (eye_l["x"] + eye_r["x"]) / 2
    eye_c_y = (eye_l["y"] + eye_r["y"]) / 2

    # 嘴中点
    mouth_c_x = (mouth_l["x"] + mouth_r["x"]) / 2
    mouth_c_y = (mouth_l["y"] + mouth_r["y"]) / 2

    # 眉心嘴巴距离
    eye_mouth_c_dis = cal_distance([eye_c_x, eye_c_y], [mouth_c_x, mouth_c_y])

    # 左脸
    eye_mouth_l_c_x = (eye_l["x"] * 4 + mouth_l["x"] * 6) / 10
    eye_mouth_l_c_y = (eye_l["y"] * 4 + mouth_l["y"] * 6) / 10

    # 右脸
    eye_mouth_r_c_x = (eye_r["x"] * 4 + mouth_r["x"] * 6) / 10
    eye_mouth_r_c_y = (eye_r["y"] * 4 + mouth_r["y"] * 6) / 10

    # 左右脸距离
    eye_mouth_l_r_dis = cal_distance([eye_mouth_l_c_x, eye_mouth_l_c_y], [eye_mouth_r_c_x, eye_mouth_r_c_y])

    nose_to_face_l_dis = distance_from_point_to_line([nose["x"], nose["y"]],
                                                     [eye_l["x"], eye_l["y"]],
                                                     [mouth_l["x"], mouth_l["y"]])

    nose_to_face_r_dis = distance_from_point_to_line([nose["x"], nose["y"]],
                                                     [eye_r["x"], eye_r["y"]],
                                                     [mouth_r["x"], mouth_r["y"]])

    nose_to_shu_dis = distance_from_point_to_line([nose["x"], nose["y"]],
                                                  [eye_c_x, eye_c_y],
                                                  [mouth_c_x, mouth_c_y])

    nose_to_top_dis = distance_from_point_to_line([nose["x"], nose["y"]],
                                                  [eye_r["x"], eye_r["y"]],
                                                  [eye_l["x"], eye_l["y"]])

    nose_to_down_dis = distance_from_point_to_line([nose["x"], nose["y"]],
                                                   [mouth_l["x"], mouth_l["y"]],
                                                   [mouth_r["x"], mouth_r["y"]])

    nose_to_heng_dis = distance_from_point_to_line([nose["x"], nose["y"]],
                                                   [eye_mouth_l_c_x, eye_mouth_l_c_y],
                                                   [eye_mouth_r_c_x, eye_mouth_r_c_y])

    xielv = cal_k([eye_mouth_l_c_x, eye_mouth_l_c_y], [eye_mouth_r_c_x, eye_mouth_r_c_y])

    euler = {}
    if nose_to_top_dis <= nose_to_down_dis:
        # euler["pitch"] = min(nose_to_heng_dis / eye_mouth_c_dis, 1)
        pitch = min(nose_to_heng_dis / eye_mouth_c_dis, 1)
    else:
        # euler["pitch"] = max(-nose_to_heng_dis / eye_mouth_c_dis, -1)
        pitch = max(-nose_to_heng_dis / eye_mouth_c_dis, -1)

    if nose_to_face_r_dis <= nose_to_face_l_dis:
        # euler["yaw"] = min(nose_to_shu_dis / eye_mouth_l_r_dis, 1)
        yaw = min(nose_to_shu_dis / eye_mouth_l_r_dis, 1)
    else:
        # euler["yaw"] = max(-nose_to_shu_dis / eye_mouth_l_r_dis, -1)
        yaw = max(-nose_to_shu_dis / eye_mouth_l_r_dis, -1)

    # euler["roll"] = math.atan(xielv) / math.pi * 2
    roll = math.atan(xielv) / math.pi * 2
    return pitch, yaw, roll
