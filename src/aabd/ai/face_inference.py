import os.path

try:
    from .face_pyr import pyr_kps
    from .face_clip import clip_face
    from .face_quality_ediffiqa import FaceQuality
except:
    from face_pyr import pyr_kps
    from face_clip import clip_face
    from face_quality_ediffiqa import FaceQuality
from insightface.app import FaceAnalysis


def load_insight_face(insightface_dir, provider='CUDA'):
    model = FaceAnalysis(root=insightface_dir, providers=[provider + 'ExecutionProvider', ])  # buffalo_l
    model.prepare(ctx_id=0, det_size=(640, 640))
    return model


class FaceModel:
    def __init__(self, insightface_dir, ediffiqa_model=None, device='cuda'):
        import torch
        if 'cuda' in device:
            provider = 'CUDA'
        else:
            provider = 'CPU'
        self.device = torch.device(device)
        self.insight_face_model = FaceAnalysis(root=insightface_dir,
                                               providers=[provider + 'ExecutionProvider', ])  # buffalo_l
        self.insight_face_model.prepare(ctx_id=0, det_size=(640, 640))

        self.detection_model = self.insight_face_model.models['detection']
        self.recognition_model = self.insight_face_model.models['recognition']

        self.face_quality_enable = ediffiqa_model is not None

        if self.face_quality_enable:
            self.face_quality_model = FaceQuality(ediffiqa_model, device)

    def predict(self, image, det=True, feature=True, quality=True, align_image=True,
                det_threshold=None,
                height_min=None, height_max=None,
                area_min=None, area_max=None,
                pyr_p_min=None, pyr_p_max=None,
                pyr_y_min=None, pyr_y_max=None,
                pyr_r_min=None, pyr_r_max=None,
                quality_min=None, quality_max=None,
                expanded_align_image=None,
                ):
        h, w, c = image.shape
        if not self.face_quality_enable:
            quality = False
            quality_min = None
            quality_max = None

        if height_min is not None and height_min < 0:
            height_min = height_min * h
        if height_max is not None and height_max < 0:
            height_max = height_max * h
        if area_min is not None and area_min < 0:
            area_min = area_min * h * w
        if area_max is not None and area_max < 0:
            area_max = area_max * h * w

        if not det:
            align_image = False
            det_threshold = None
            height_min = None
            height_max = None
            area_min = None
            area_max = None
            pyr_p_min = None
            pyr_p_max = None
            pyr_y_min = None
            pyr_y_max = None
            pyr_r_min = None
            pyr_r_max = None
            quality_min = None
            quality_max = None
            expanded_align_image = None
        faces = []
        if det:
            det, kpss = self.detection_model.detect(image)
            faces = [
                {"box": list(map(int, d[0][:4])), "det_score": float(d[0][4]), "kpss": d[1], 'pyr': pyr_kps(d[1])}
                for d in
                zip(det, kpss)]
        else:
            faces.append({"align_image": image})
        if det_threshold:
            faces = [face for face in faces if face['det_score'] >= det_threshold]
        if height_min:
            faces = [face for face in faces if face['box'][3] - face['box'][1] >= height_min]
        if height_max:
            faces = [face for face in faces if face['box'][3] - face['box'][1] <= height_max]
        if area_min:
            faces = [face for face in faces if
                     (face['box'][2] - face['box'][0]) * (face['box'][3] - face['box'][1]) >= area_min]
        if area_max:
            faces = [face for face in faces if
                     (face['box'][2] - face['box'][0]) * (face['box'][3] - face['box'][1]) <= area_max]
        if pyr_p_min:
            faces = [face for face in faces if face['pyr'][0] >= pyr_p_min]
        if pyr_p_max:
            faces = [face for face in faces if face['pyr'][0] <= pyr_p_max]
        if pyr_y_min:
            faces = [face for face in faces if face['pyr'][1] >= pyr_y_min]
        if pyr_y_max:
            faces = [face for face in faces if face['pyr'][1] <= pyr_y_max]
        if pyr_r_min:
            faces = [face for face in faces if face['pyr'][2] >= pyr_r_min]
        if pyr_r_max:
            faces = [face for face in faces if face['pyr'][2] <= pyr_r_max]

        if feature or align_image or quality:
            for face in faces:
                face['align_image'] = clip_face(image, face['kpss'])[0]

        if quality:
            for face in faces:
                face['quality'] = self.face_quality_model.predict(face['align_image'])[0]
            if quality_min:
                faces = [face for face in faces if face['quality'] >= quality_min]
            if quality_max:
                faces = [face for face in faces if face['quality'] <= quality_max]

        if expanded_align_image and len(expanded_align_image) == 5:
            for face in faces:
                face['expanded_align_image'] = clip_face(image, face['kpss'], face['pyr'][1], *expanded_align_image)
        if feature:
            for face in faces:
                face['feature'] = self.recognition_model.get_feat(face['align_image'])[0]

        if not align_image:
            for face in faces:
                face.pop('align_image')
        return faces

    def __call__(self, *args, **kwargs):
        return self.predict(*args, **kwargs)
