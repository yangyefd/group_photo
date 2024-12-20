import os
from PIL import Image,ImageDraw,ImageFont
import pickle
from sklearn.cluster import DBSCAN
import numpy as np
import glob

def load_face_bank(face_folder, face_recognizer, use_cache=True):
    cache_path = 'facebank.cache'
    if use_cache and os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    bank = []
    img_paths = glob.glob(os.path.join(face_folder, '**/**.**'))
    # img_paths = glob.glob(os.path.join(face_folder, '**.**'))
    # 遍历已知人脸图片
    for img_path in img_paths:
        _, ext = os.path.splitext(img_path)
        if ext not in ['.jpg', '.jpeg', '.png']:
            continue
        # 获取人名
        name = os.path.basename(os.path.dirname(img_path))
        img = Image.open(img_path)
        img = img.convert('RGB')
        embeddings = face_recognizer(img)['img_embedding']
        if len(embeddings) == 0:
            continue
        bank.append({
            "name": name,
            "embedding": embeddings[0]
        })
    # 缓存特征库
    with open(cache_path, 'wb') as f:
        pickle.dump(bank, f)
    return bank

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

def get_face_img_box(image, box):
    w = box[2] - box[0]
    h = box[3] - box[1]
    x0 = box[0]
    if x0 < 0:
        x0 = 1
    y0 = box[1]
    if y0 < 0:
        y0 = 1
    x1 = box[2]
    if x1 > image.width:
        x1 = image.width - 1
    y1 = box[3]
    if y1 > image.height:
        y1 = image.height - 1
    return image.crop((x0, y0, x1, y1))

def get_face_embedding(image, box, face_recognizer):
    face_img = get_face_img(image, box)
    embeddings = face_recognizer(face_img)['img_embedding']
    if len(embeddings) == 0:
        return None
    return embeddings[0], face_img

def get_name_sim(face_embedding, face_bank):
    name = ''
    maxSim = 0
    for face in face_bank:
        sim = np.dot(face_embedding, face['embedding'])
        if sim > maxSim:
            maxSim = sim
            name = face['name']
    return name, maxSim

def draw_face(img_draw, face, font):
    box = face['box']
    name = face['name']
    sim = face['sim']
    row = face['row']

    row_size = min(box[2] - box[0], box[3] - box[1]) // 2
    # 创建一个字体对象
    font_row = ImageFont.truetype('arial.ttf', row_size)
    # 要绘制的文本
    text = str(row)  # 将数字转换为字符串
    # 获取文本的边界框
    bbox = img_draw.textbbox((0, 0), text, font=font_row)
    # 计算文本的位置，使其在矩形框内居中
    x = box[0] + (box[2] - box[0] - bbox[2]) / 2
    y = box[1] + (box[3] - box[1] - bbox[3]) / 2
    # 在图像上绘制文本
    img_draw.text((x, y), text, font=font_row, fill=(0, 0, 255))

    line_thickness = max(1,int(min(img_draw.im.size) / 500))
    img_draw.text((box[0], box[1]-30), name, fill=(0, 0, 255), font=font)
    img_draw.rectangle([box[0], box[1], box[2], box[3]], outline ='red',width=line_thickness) 

def draw_faces(image, faces):
    font = ImageFont.truetype("Microsoft YaHei UI Bold.ttf", 20, encoding="unic")
    draw = ImageDraw.Draw(image)
    for face in faces:
        draw_face(draw, face, font)

def draw_face_emoji(img_draw, face, emoji_dict):
    box = face['box']
    w, h = box[2] - box[0], box[3] - box[1]
    x, y = box[0], box[1]
    w, h, x, y = int(w), int(h), int(x), int(y)
    resize_len = max(w, h)
    emoji_img = emoji_dict[face['emotion_state']]
    mask_img = emoji_dict['mask']
    # Resize emoji to fit inside the face box
    x += (w - resize_len) // 2
    if x < 0:
        x = 0
    y += (h - resize_len) // 2
    if y < 0:
        y = 0
    emoji_resized = emoji_img.resize((resize_len, resize_len))
    mask_resized = mask_img.resize((resize_len, resize_len)).convert('L')

    # Convert the emoji image to a numpy array
    emoji_np = np.array(emoji_resized)
    mask_np = np.array(mask_resized)

    # Check if the emoji has an alpha channel (transparency)
    if emoji_np.shape[2] == 3:
        # Split the emoji channels
        emoji_bgr = emoji_np[:, :, :3]  # BGR channels (ignoring alpha)
        
        # Place the emoji on the face region in the frame
        for c in range(3):
            img_draw[y:y+resize_len, x:x+resize_len, c][mask_np < 10] = emoji_bgr[:, :, c][mask_np < 10]
    return img_draw


def draw_faces_emoji(image, faces, emoji_dict):
    draw = np.array(image)
    for face in faces:
        draw = draw_face_emoji(draw, face, emoji_dict)
    image = Image.fromarray(draw)
    return image

def get_rownum(data, mean_h, result):
    # 使用y坐标作为距离度量值
    dbscan = DBSCAN(eps=mean_h*0.6, min_samples=4)
    labels = dbscan.fit_predict(data[:,1:2])
    #检查混叠
    for i in range(max(labels)+1):
        columns = []
        for j in range(len(data)):
            if i == labels[j]:
                # 加入对应排
                columns.append((data[j]))
        columns_np = np.array(columns)
        # 排内按照x坐标排序
        x_sort= np.sort(columns_np[:,2])
        x_diff = np.diff(x_sort)
        if min(x_diff) < mean_h*0.6:
            get_rownum(columns_np, mean_h*0.8, result)
        else:
            result.append(columns_np[:,0].tolist())

def get_rows(faces):
    # 获取人脸检测框高度的平均值，作为DBSCAN算法的eps参数
    boxes = [face['box'] for face in faces]
    mean_h = get_mean_height(boxes)
    ys = [(box[1] + box[3])//2 for box in boxes]
    xs = [(box[0] + box[1])//2 for box in boxes]
    # 使用y坐标作为距离度量值
    order = np.expand_dims(np.arange(len(ys)), axis=1)
    datay = np.expand_dims(np.array(ys), axis=1)
    datax = np.expand_dims(np.array(xs), axis=1)
    data = np.concatenate((order, datay, datax), axis=1)
    result = []
    get_rownum(data, mean_h, result)
    # dbscan = DBSCAN(eps=mean_h*0.6, min_samples=4)
    # # 获取到每个度量值对应的类别
    # labels = dbscan.fit_predict(data)
    labels = []
    for i in range(len(ys)):
        labels_one = -1
        for j in range(len(result)):
            if i in result[j]:
                labels_one = j
                break
        labels.append(labels_one)
        
    for i in range(len(faces)):
        faces[i].update({'row': labels[i]})
    rows = []
    # 聚类出来的类别数即为排数
    for i in range(max(labels)+1):
        columns = []
        top = 0
        for j in range(len(boxes)):
            if i == labels[j]:
                # 加入对应排
                columns.append((boxes[j][0], j))
                top += boxes[j][1]
        # 排内按照x坐标排序
        columns.sort(key=lambda x: x[0])
        rows.append((top // len(columns), [item[1] for item in columns]))
        # 排按照y坐标排序
        rows.sort(key=lambda x: x[0])
    return [row[1] for row in rows]

def draw_name(img, row_names):
    line_space = 40
    bottom_shift = 120
    # 使用中文字体
    font = ImageFont.truetype("Microsoft YaHei UI Bold.ttf", 30, encoding="unic")
    draw = ImageDraw.Draw(img)
    height_count = 0
    for row_name in row_names:
        y = img.height - bottom_shift + height_count * line_space
        name_str = ''
        for name in row_name:
            name_str += f'{name}   '
        name_str = name_str.strip()
        # 计算人名字符串渲染到图片中所占的长度
        text_len = draw.textlength(name_str, font)
        x = (img.width - text_len) //2
        # 将人名字符串居中渲染到图片中
        draw.text((x, y), name_str, fill=(0, 128, 0), font=font)
        height_count += 1
    return img

def get_row_names(faces, rows):
    row_names = []
    for row in rows:
        row_name = []
        for index in row:
            row_name.append(faces[index]['name'])
        row_names.append(row_name)
    return row_names

def get_row_names_text(row_names):
    text = ''
    for row_name in row_names:
        for name in row_name:
            text += f'{name}   '
        text += '\n'
    return text.rstrip('\n')

def get_mean_height(boxes):
    h_sum = 0
    for box in boxes:
        h_sum += box[3] - box[1]
    return h_sum // len(boxes)

def resize_img(img):
    ratio = img.width / 1000
    if ratio < 1:
        return img
    w_new = int(img.width / ratio)
    h_new = int(img.height / ratio)
    return img.resize((w_new, h_new), resample=Image.BILINEAR)   

def resize_img_t(img):
    ratio = img.width / 1000
    if ratio < 1:
        return img, 1
    w_new = int(img.width / ratio)
    h_new = int(img.height / ratio)
    return img.resize((w_new, h_new), resample=Image.BILINEAR), ratio
