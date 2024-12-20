from util import *
import json
from modelscope.outputs import OutputKeys

def nms(faces_list, iou_threshold=0.5):
    """
    非极大值抑制（Non-Maximum Suppression, NMS）
    
    参数:
    faces: list of tuples
        每个元组包含 (x1, y1, x2, y2, score)，表示一个检测框及其置信度分数
    iou_threshold: float
        交并比（Intersection over Union, IoU）的阈值，用于判断两个框是否重叠
        
    返回:
    list of tuples
        经过 NMS 处理后的检测框列表
    """
    if len(faces_list) == 0:
        return []

    boxes = [faces_i['box'] for faces_i in faces_list]
    scores = [faces_i['score'] for faces_i in faces_list]
    boxes = np.array(boxes)
    scores = np.array(scores)
    # 将检测框转换为 numpy 数组
    faces = np.hstack((boxes, scores[:, np.newaxis]))
    
    # 按照置信度分数降序排序
    sorted_indices = np.argsort(faces[:, 4])[::-1]
    faces = faces[sorted_indices]

    # 用于存储保留的检测框索引
    keep = []

    while faces.shape[0] > 0:
        # 保留置信度最高的检测框
        keep.append(faces[0])
        
        # 计算当前检测框与其他检测框的 IoU
        x1 = np.maximum(faces[0, 0], faces[1:, 0])
        y1 = np.maximum(faces[0, 1], faces[1:, 1])
        x2 = np.minimum(faces[0, 2], faces[1:, 2])
        y2 = np.minimum(faces[0, 3], faces[1:, 3])
        
        intersection = np.maximum(0, x2 - x1 + 1) * np.maximum(0, y2 - y1 + 1)
        area = (faces[0, 2] - faces[0, 0] + 1) * (faces[0, 3] - faces[0, 1] + 1)
        area_other = (faces[1:, 2] - faces[1:, 0] + 1) * (faces[1:, 3] - faces[1:, 1] + 1)
        
        iou = intersection / (area + area_other - intersection)
        
        # 保留 IoU 小于阈值的检测框
        indices_to_keep = np.where(iou <= iou_threshold)[0]
        faces = faces[indices_to_keep + 1]

    return keep

def nms_facearea(faces_list, iou_threshold=0.5, same_person_threshold=0.75):
    """
    非极大值抑制（Non-Maximum Suppression, NMS）
    
    参数:
    faces: list of tuples
        每个元组包含 (x1, y1, x2, y2, score)，表示一个检测框及其置信度分数
    iou_threshold: float
        交并比（Intersection over Union, IoU）的阈值，用于判断两个框是否重叠
        
    返回:
    list of tuples
        经过 NMS 处理后的检测框列表
    """
    if len(faces_list) == 0:
        return []
    #用脸的面积作为分数
    boxes = [faces_i['box'] for faces_i in faces_list]
    scores = [(box_i[2]-box_i[0])*(box_i[3]-box_i[1]) for box_i in boxes]
    boxes = np.array(boxes)
    scores = np.array(scores)
    # 将检测框转换为 numpy 数组
    faces = np.hstack((boxes, scores[:, np.newaxis]))
    
    # 按照置信度分数降序排序
    sorted_indices = np.argsort(faces[:, 4])[::-1]
    faces = faces[sorted_indices]

    # 用于存储保留的检测框索引
    keep = []

    while faces.shape[0] > 0:
        # 保留置信度最高的检测框
        keep.append(faces[0])
        
        # 计算当前检测框与其他检测框的 IoU
        x1 = np.maximum(faces[0, 0], faces[1:, 0])
        y1 = np.maximum(faces[0, 1], faces[1:, 1])
        x2 = np.minimum(faces[0, 2], faces[1:, 2])
        y2 = np.minimum(faces[0, 3], faces[1:, 3])
        
        intersection = np.maximum(0, x2 - x1 + 1) * np.maximum(0, y2 - y1 + 1)
        area = (faces[0, 2] - faces[0, 0] + 1) * (faces[0, 3] - faces[0, 1] + 1)
        area_other = (faces[1:, 2] - faces[1:, 0] + 1) * (faces[1:, 3] - faces[1:, 1] + 1)
        
        iou = intersection / (area + area_other - intersection)
        same_person = intersection / (np.minimum(np.expand_dims(area, axis=0), area_other) + 1e-6)
        same_person = same_person > same_person_threshold
        
        # 保留 IoU 小于阈值的检测框
        indices_to_keep = np.where(iou <= iou_threshold)[0]
        indices_to_keep = indices_to_keep[~same_person[indices_to_keep]]
        faces = faces[indices_to_keep + 1]

    return keep

def split_image_with_overlap(image, patch_size=512, overlap_rate=0.25):
    """
    将图像切分为重叠的块，并返回所有块及其在原图中的坐标
    
    参数:
    - image: 输入图像 (NumPy数组)
    - patch_size: 每个块的大小 
    - overlap_rate: 重叠率 (0-1之间)
    
    返回:
    - patches: 图像块列表
    - coordinates: 每个图像块的原始坐标 [(x_start, y_start, x_end, y_end)]
    """
    # 获取图像尺寸
    height, width = image.shape[:2]
    
    # 计算滑动步长
    step = int(patch_size * (1 - overlap_rate))
    
    # 存储图像块和坐标的列表
    patches = []
    coordinates = []
    
    # 遍历图像
    for y in range(0, height, step):
        for x in range(0, width, step):
            # 确定块的结束坐标
            x_end = min(x + patch_size, width)
            y_end = min(y + patch_size, height)
            
            # 提取图像块
            patch = image[y:y_end, x:x_end]
            
            # 处理边缘情况，确保块大小一致
            if patch.shape[0] == patch_size and patch.shape[1] == patch_size:
                patches.append(patch)
                coordinates.append((x, y, x_end, y_end))
            elif x + patch_size > width or y + patch_size > height:
                # 对于边缘块，使用填充或裁剪方式
                if patch.shape[0] < patch_size or patch.shape[1] < patch_size:
                    # 创建全零块并填充原始图像块
                    padded_patch = np.zeros((patch_size, patch_size, image.shape[2]) if len(image.shape) == 3 else (patch_size, patch_size), dtype=image.dtype)
                    padded_patch[:patch.shape[0], :patch.shape[1]] = patch
                    patches.append(padded_patch)
                    coordinates.append((x, y, x_end, y_end))
    
    return np.array(patches), coordinates

class detector():
    def __init__(self, face_detector, detect_threshold):
        self.face_detector = face_detector
        self.detect_threshold = detect_threshold
        self.img_patches = None
        self.coordinates = None
        self.boxes = []

    def split_image(self, img_big, patch_size=512, overlap_rate=0.25):
        img_big_np = np.array(img_big)
        self.img_patches, self.coordinates = split_image_with_overlap(img_big_np, patch_size=512, overlap_rate=0.25)
    
    def detect(self, img_np, coordinates_i):
        img = Image.fromarray(img_np)
        img, ratio = resize_img_t(img)
        img = img.convert('RGB') 
        detection_result = self.face_detector(img)
        boxes = np.array(detection_result[OutputKeys.BOXES]) # L, U, R, D
        scores = np.array(detection_result[OutputKeys.SCORES])
        for i in range(len(boxes)):
            score = scores[i]
            if score < self.detect_threshold:
                continue
            box = boxes[i]*ratio
            box[0] += coordinates_i[0]
            box[1] += coordinates_i[1]
            box[2] += coordinates_i[0]
            box[3] += coordinates_i[1]
            self.boxes.append({'box': box, 'score': score})

    def nms_facearea(self):
        self.boxes = nms_facearea(self.boxes)

class recognizer():
    def __init__(self, face_recognizer, face_bank, sim_threshold):
        self.face_recognizer = face_recognizer
        self.face_bank = face_bank
        self.sim_threshold = sim_threshold
        self.faces = []

    def face_recognize(self, boxes, img):
        
        for i in range(len(boxes)):
            box = boxes[i][:4]
            face_embedding, face_img = get_face_embedding(img, box, self.face_recognizer)
            name, sim = get_name_sim(face_embedding, self.face_bank)
            if name is None:
                continue
            # face_img = get_face_img_box(img, box)
            if sim < self.sim_threshold:
                self.faces.append({'box': box, 'name': '未知', 'sim': sim, 'face_img':face_img})
            else:
                self.faces.append({'box': box, 'name': name, 'sim': sim, 'face_img':face_img})

# def detect(img_big, face_detector, draw_detect_enabled, detect_threshold):
#     img_big_np = np.array(img_big)
#     img_patches, coordinates = split_image_with_overlap(img_big_np, patch_size=512, overlap_rate=0.25)
#     faces = []
#     for idx, img_np in enumerate(img_patches):
#         img = Image.fromarray(img_np)
#         coordinates_i = coordinates[idx]
#         img, ratio = resize_img_t(img)
#         img = img.convert('RGB') 
#         detection_result = face_detector(img)
#         boxes = np.array(detection_result[OutputKeys.BOXES]) # L, U, R, D
#         scores = np.array(detection_result[OutputKeys.SCORES])
#         for i in range(len(boxes)):
#             score = scores[i]
#             if score < detect_threshold:
#                 continue
#             box = boxes[i]*ratio
#             box[0] += coordinates_i[0]
#             box[1] += coordinates_i[1]
#             box[2] += coordinates_i[0]
#             box[3] += coordinates_i[1]
#             faces.append({'box': box, 'score': score})
#     #nms faces
#     faces = nms_facearea(faces)

#     return faces
    