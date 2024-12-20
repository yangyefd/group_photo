from PIL import Image,ImageDraw, ImageFont
import numpy as np
def resize_img(img):
    ratio = img.width / 1000
    if ratio < 1:
        return img
    w_new = int(img.width / ratio)
    h_new = int(img.height / ratio)
    return img.resize((w_new, h_new), resample=Image.BILINEAR)
left_eye_start = 66 #左眼特征点起始位置
left_eye_end = 73   #左眼特征点结束位置
rigth_eye_start = 75 #右眼特征点起始位置
rigth_eye_end = 82   #右眼特征点结束位置
eye_ratio = 0.1      #眼睛纵横比阈值，经测试阈值与照片大小成反比
def get_face_img(image, box):
    w = box[2] - box[0]
    h = box[3] - box[1]
    x0 = box[0] - w//2
    if x0 < 0:
        x0 = 1
    y0 = box[1] - h//2
    if y0 < 0:
        y0 = 1
    x1 = box[2] + w//2
    if x1 > image.width:
        x1 = image.width - 1
    y1 = box[3] + h//2
    if y1 > image.height:
        y1 = image.height - 1
    return image.crop((x0, y0, x1, y1))
def get_faces(img):
    #img = resize_img(img)
    img = img.convert('RGB')
    result = face_detector(img)
    images = []
    imc =ImageDraw.Draw(img)
    for i in range(len(result['boxes'])):
        box = result['boxes'][i]
        face = get_face_img(img, box)
        images.append(face)
        imc.rectangle([box[0], box[1], box[2], box[3]], outline ='red')
    #img.show()
    return images,result['boxes']
def get_emotion(img, emotion):
    img = img.resize((128, 128), Image.Resampling.BILINEAR)#将图片大小调整为64x64
    result = emotion(img)
    label_idx = np.array(result['scores']).argmax()#输出情绪分类中概率最大的为情绪标签
    label = result['labels'][label_idx]
    return label

def draw_emotion_labels(img, boxes, emotions):
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 16)  # 选择合适的字体和大小
    for box, emotion in zip(boxes, emotions):
        draw.rectangle(box, outline="red", width=2)  # 画人脸框
        draw.text((box[0], box[3]), emotion, fill="red", font=font)  # 在人脸下方标注情感标签
    return img
def draw_eyestate_labels(img, boxes, eyestates):
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 16)  # 选择合适的字体和大小
    for box, eyestate in zip(boxes, eyestates):
        draw.rectangle(box, outline="red", width=2)  # 画人脸框
        draw.text((box[0], box[3]+20),  eyestate, fill="red", font=font)  # 在人脸下方标注眼睛状态标签
    return img
def compute_eye_aspect_ratio(eye): #计算眼睛纵横纵横比 A.B为垂直距离  C为水平距离
    A = np.linalg.norm(eye[1] - eye[7])
    B = np.linalg.norm(eye[3] - eye[5])
    C = np.linalg.norm(eye[0] - eye[4])
    ear = (A + B) / (2.0 * C)
    return ear
def eyeclosed(img, face_2d_keypoints):
    # img = img.resize((64, 64), Image.Resampling.BILINEAR)
    result = face_2d_keypoints(img)
    eye_left = result["keypoints"][0][left_eye_start:left_eye_end+1]
    eye_right = result["keypoints"][0][rigth_eye_start:rigth_eye_end+1]
    le = compute_eye_aspect_ratio(eye_left)
    re = compute_eye_aspect_ratio(eye_right)
    eye = (le+re)/2.0 #计算两只眼平均值
    return eye 

def wheather_smile(imgsrc,imgs,boxes):
    unhappy_boxes =[] 
    closed_eye_boxes = []
    unhappy_counts = 0 # 不开心的人数计数器
    closed_eye_counts = 0 # 闭眼的人数计数器
    unhappy_states =[] # 不开心的人的情绪状态
    eye_rates = []  #闭眼的人的眼睛状态
    for img in imgs:
        emotion = get_emotion(img)
        eye_rate = eyeclosed(img)
        if emotion in ['Angry', 'Disgust', 'Fear', 'Sad']:# 判定为不开心的情绪种类
            unhappy_boxes.append(boxes[imgs.index(img)])
            unhappy_counts += 1
            unhappy_states.append("unhappy")
        if eye_rate < eye_ratio:
            closed_eye_boxes.append(boxes[imgs.index(img)])
            closed_eye_counts += 1
            eye_rates.append("closed")
    img_with_label1 = draw_emotion_labels(imgsrc, unhappy_boxes, unhappy_states)# 画出不开心的人
    img_with_label2 = draw_eyestate_labels(img_with_label1, closed_eye_boxes, eye_rates)# 画出闭眼的人
    print("Number of people with closed eyes:", closed_eye_counts)
    print("Number of people who are not happy:", unhappy_counts)
    return img_with_label2

