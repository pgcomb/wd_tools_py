import cv2
import numpy as np
from skimage import transform as trans

arcface_dst = np.array(
    [[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366],
     [41.5493, 92.3655], [70.7299, 92.2041]],
    dtype=np.float32)


def clip_face(image, src_kps=None, yaw=0.0, face_size=112, top_offset=0, down_offset=0, left_offset=0, right_offset=0,
              strict_align=False):
    face_ratio = face_size / 112
    offset_x = left_offset
    if not strict_align:
        offset_x = offset_x + 30 * face_ratio * yaw
    dest_kps = np.array(
        [[38.2946 * face_ratio + offset_x, 51.6963 * face_ratio + top_offset],
         [73.5318 * face_ratio + offset_x, 51.5014 * face_ratio + top_offset],
         [56.0252 * face_ratio + offset_x, 71.7366 * face_ratio + top_offset],
         [41.5493 * face_ratio + offset_x, 92.3655 * face_ratio + top_offset],
         [70.7299 * face_ratio + offset_x, 92.2041 * face_ratio + top_offset]],
        dtype=np.float32)
    tform = trans.SimilarityTransform()
    tform.estimate(src_kps, dest_kps)
    M = tform.params[0:2, :]
    warped = cv2.warpAffine(image, M, (face_size + left_offset + right_offset, face_size + top_offset + down_offset),
                            borderValue=0.0)
    return warped, M
