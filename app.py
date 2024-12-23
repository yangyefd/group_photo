# import gradio as gr
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from modelscope.outputs import OutputKeys
from PIL import Image
import json
import os
import numpy as np
from util import *
from detect_recognize import detector, recognizer
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QInputDialog, QMessageBox, QVBoxLayout, QPushButton, QDialog, QTextEdit
from PySide6.QtWidgets import QButtonGroup, QGraphicsScene, QGraphicsPixmapItem, QFileDialog, QLabel, QTableWidgetItem, QHeaderView
from PySide6.QtGui import QIcon, QPixmap, QImage
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWebEngineWidgets import QWebEngineView
# 导入我们生成的界面
from ui.main_ui import Ui_Dialog
import copy
import cv2
from emotion import get_emotion, eyeclosed
facebank_path = 'images/facebank'
face_detector = pipeline(Tasks.face_detection, model='gaosheng/face_detect') #人脸检测
# face_recognizer = pipeline(Tasks.face_recognition, model='damo/cv_ir101_facerecognition_cfglint')
face_recognizer = pipeline(Tasks.face_recognition, model='iic/cv_ir101_facerecognition_cfglint') #人脸识别
portrait_matting = pipeline(Tasks.portrait_matting, model='damo/cv_unet_image-matting') #人脸抠图
face_2d_keypoints_model = pipeline(Tasks.face_2d_keypoints, model='damo/cv_mobilenet_face-2d-keypoints_alignment') #闭眼检测
emotion_model = pipeline(Tasks.facial_expression_recognition, 'damo/cv_vgg19_facial-expression-recognition_fer') #表情识别
face_bank = load_face_bank(facebank_path, face_recognizer)

#查找人名并搜索头像
def get_enlarged_face_img(image, box, scale=3):
    w = box[2] - box[0]
    h = box[3] - box[1]
    # 计算新的边界框坐标
    x0 = max(box[0] - (scale - 1.6) * w // 2, 0)
    y0 = max(box[1] - (scale - 1.2) * h // 2, 0)
    x1 = min(box[2] + (scale - 1.6) * w // 2, image.width)
    y1 = min(box[3] + (scale - 1.2) * h // 2, image.height)

    return image.crop((x0, y0, x1, y1))

class ImageDialog(QDialog):
    def __init__(self, image, file_name='segmented_image.png', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Display Image")
        self.file_name = file_name  # Default file name for saving
        # Layout
        layout = QVBoxLayout()
        self.image = image
        
        # Label to display image
        self.image_label = QLabel(self)
        
        # Convert OpenCV image (BGR) to QImage (RGB)
        height, width, channels = image.shape
        bytes_per_line = channels * width
        q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(q_image)

        # Set pixmap to the label
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        # Add label to layout
        layout.addWidget(self.image_label)
        
        # Save Button
        self.save_button = QPushButton("Save Image", self)
        self.save_button.clicked.connect(self.save_image)
        layout.addWidget(self.save_button)
        
        self.setLayout(layout)

    def save_image(self):
        # Open file dialog to choose location to save
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Image", self.file_name, "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)")
        if file_name:
            # Save the image to the specified file path
            # Convert to PIL Image
            pil_image = Image.fromarray(self.image).convert("RGBA")
            # Save the image using Pillow
            pil_image.save(file_name)
            # cv2.imwrite(file_name, cv2.cvtColor(self.image, cv2.COLOR_RGBA2BGRA))  # Convert back to BGR for saving
            print(f"Image saved to {file_name}")

class Detect_Worker(QThread):
    progress = Signal(int)  # 自定义信号，用于更新进度条
    finished = Signal()  # 自定义信号，用于通知线程完成

    def __init__(self, detector, recognizer, img):
        super().__init__()
        self.detector = detector  # 保存传入的参数
        self.recognizer = recognizer  # 保存传入的参数
        self.img = img  # 保存传入的参数

    def run(self):
        img_patches, coordinates = self.detector.img_patches, self.detector.coordinates
        for idx, img_np in enumerate(img_patches):
            self.detector.detect(img_np, coordinates[idx])
            self.progress.emit((idx)/len(img_patches)*100)  # 发射进度信号
        # 任务完成后发射信号
        self.finished.emit()

class Emotion_Worker(QThread):
    progress = Signal(int)  # 自定义信号，用于更新进度条
    finished = Signal()  # 自定义信号，用于通知线程完成

    def __init__(self, recognizer, eye_ratio):
        super().__init__()
        self.recognizer = recognizer  # 保存传入的参数
        self.eye_ratio = eye_ratio  # 保存传入的参数

    def run(self):
        for idx, item in enumerate(self.recognizer.faces):
            face_img = item['face_img']
            emotion = get_emotion(face_img, emotion_model)
            eye_rate = eyeclosed(face_img, face_2d_keypoints_model)
            emotion_flag = 0
            eye_flag = 0
            if emotion in ['Angry', 'Disgust', 'Fear', 'Sad']:# 判定为不开心的情绪种类
                emotion_flag = 1
            if eye_rate < self.eye_ratio:
                eye_flag = 1
            if emotion_flag == 0 and eye_flag == 0:
                self.recognizer.faces[idx].update({'emotion_state':'open_happy'})
            if emotion_flag == 0 and eye_flag == 1:
                self.recognizer.faces[idx].update({'emotion_state':'close_happy'})
            if emotion_flag == 1 and eye_flag == 0:
                self.recognizer.faces[idx].update({'emotion_state':'open_unhappy'})
            if emotion_flag == 1 and eye_flag == 1:
                self.recognizer.faces[idx].update({'emotion_state':'close_unhappy'})
            self.progress.emit((idx)/len(self.recognizer.faces)*100)  # 发射进度信号
        # 任务完成后发射信号
        self.finished.emit()

# 继承QWidget类，以获取其属性和方法
class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        # 设置界面为我们生成的界面
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.file_process_finished = False
        self.image_order_path = 'images/result.jpg'
        self.image_emotion_path = 'images/emotion.jpg'

        self.scene = QGraphicsScene(self)
        self.ui.graphicsView.setScene(self.scene)
        self.ui.graphicsView.wheelEvent = self.graphicsView_wheelEvent  # 绑定自定义的滚轮事件处理函数
        # 设置鼠标跟踪
        self.ui.graphicsView.setMouseTracking(True)
        self.ui.graphicsView.mousePressEvent = self.graphicsView_mousePressEvent  # 绑定自定义的鼠标点击事件处理函数


        self.ui.user_name.setPlaceholderText("enter name")
        # 将 QLineEdit 的 returnPressed 信号连接到槽函数
        self.ui.user_name.returnPressed.connect(self.search)

        self.ui.user_info.setReadOnly(True)
        self.ui.file_button.clicked.connect(self.read_file_dialog)
        # 将按钮添加到按钮组
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.ui.radioButton_ori)
        self.button_group.addButton(self.ui.radioButton_order)
        self.button_group.addButton(self.ui.radioButton_emotion)
        # 设置默认选项
        self.ui.radioButton_ori.setChecked(True)
        # 连接按钮的点击事件
        self.ui.radioButton_ori.toggled.connect(self.show_ori)
        self.ui.radioButton_order.toggled.connect(self.show_order)
        self.ui.radioButton_emotion.toggled.connect(self.show_emotion)

        self.ui.order_button.clicked.connect(self.order)
        self.ui.emotion_button.clicked.connect(self.emotion)
        self.emoji_dict = {
            "open_happy": Image.open("assets/emotion/open_happy.png"),
            "close_happy": Image.open("assets/emotion/close_happy.png"),
            "open_unhappy": Image.open("assets/emotion/open_unhappy.png"),
            "close_unhappy": Image.open("assets/emotion/close_unhappy.png"),
            'mask': Image.open("assets/emotion/mask.png") #mask emoji区域
        }
        self.image = None
        self.image_result = None
        self.image_emotion = None
        # 存储原始缩放级别
        self.originalScale = 1.0
        self.eye_ratio = 0.1

    def graphicsView_wheelEvent(self, event):
        # 获取滚轮的滚动量
        delta = event.angleDelta().y()
        
        # 根据滚轮的方向来放大或缩小
        if delta > 0:
            # 放大
            self.ui.graphicsView.scale(1.1, 1.1)
        else:
            # 缩小
            self.ui.graphicsView.scale(0.9, 0.9)
        
        # 更新视图
        self.ui.graphicsView.update()
    
    def resetViewScale(self):
        # 重置视图到原始大小
        currentScale = self.ui.graphicsView.transform().m11()
        # 计算缩放因子以还原到原始大小
        scaleFactor = self.originalScale / currentScale
        self.ui.graphicsView.scale(scaleFactor, scaleFactor)
        self.ui.graphicsView.update()

    def graphicsView_mousePressEvent(self, event):
        # 这里是自定义的鼠标点击事件处理逻辑
        if event.button() == Qt.LeftButton:
            # 获取鼠标点击的视口坐标
            viewPos = event.pos()
            
            # 将视口坐标转换为场景坐标
            scenePos = self.ui.graphicsView.mapToScene(viewPos)
            
            # 将视口坐标转换为场景坐标
            scenePos = self.ui.graphicsView.mapToScene(viewPos)
            for item in self.recognizer.faces:
                box = item['box']
                x0, y0, x1, y1 = box
                if x0 <= scenePos.x() <= x1 and y0 <= scenePos.y() <= y1:
                    face_segment = self.extract_faces(self.image, box)
                    self.show_image_dialog(face_segment, item['name'])
                    # 使用场景坐标进行后续处理
                    print(f"Scene coordinates: {scenePos.x()}, {scenePos.y()}")
                    break
            else: # 如果没有找到匹配的框，则重置视图
                self.resetViewScale()
            # 使用场景坐标进行后续处理
            print(f"Scene coordinates: {scenePos.x()}, {scenePos.y()}")

        elif event.button() == Qt.RightButton:
            # 处理右键点击事件
            self.resetViewScale()
            print("Right mouse button clicked")
        # 可以根据需要添加更多的事件处理

    def show_image_dialog(self, image, name):
        dialog = ImageDialog(image, name, self)
        dialog.exec()

    def show_ori(self):
        if self.image is not None:
            self.load_image(self.image)
    def show_order(self):
        if self.image_result is not None:
            self.load_image(self.image_result)
    def show_emotion(self):
        if self.image_emotion is not None:
            self.load_image(self.image_emotion)
    
    def search(self):
        # 获取输入框中的文本
        name = self.ui.user_name.text()
        
        for index, row in enumerate(self.row_name, start=1):
            row_num = len(self.row_name) - index + 1
            for col_num, name_i in enumerate(row, start=1):
                if name in name_i:
                    self.ui.user_info.setText(f"{name} is in row {row_num}, column {col_num}")
                    for item in self.recognizer.faces:
                        if item['name'] == name_i:
                            box = item['box']
                            face_segment = self.extract_faces(self.image, box)
                            self.show_image_dialog(face_segment, name_i)
                            return
                    # face_segment = self.extract_faces(self.image, box)
                    # self.show_image_dialog(face_segment, item['name'])
                    # return

        self.ui.user_info.setText(f"{name} not found")
    
    def read_file_dialog(self):
        # 打开文件对话框，让用户选择文件
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Image Files (*.png *.jpg *.jpeg)")
        self.image = None
        self.image_result = None
        self.image_emotion = None
        self.emotion_process_finished = False
        # 如果用户选择了文件，则显示文件路径
        if file_path:
            self.detector = detector(face_detector, 0.5)
            self.recognizer = recognizer(face_recognizer, face_bank, 0.3)
            self.image_path = file_path
            self.image = Image.open(file_path)
            self.load_image(self.image)
            self.image_result = copy.deepcopy(self.image)

            self.set_ui_disabled(True)
            # 设置覆盖光标，指示正在处理
            # QApplication.setOverrideCursor(Qt.WaitCursor)

            self.detector.split_image(self.image)
            self.worker = Detect_Worker(self.detector, self.recognizer, self.image)
            self.worker.progress.connect(self.update_progress)  # 连接信号到槽函数
            self.worker.finished.connect(self.on_thread_finished)  # 连接线程完成信号
            self.file_process_finished = False
            self.worker.start()
    
    def load_image(self, pil_image):
        # Clear previous scene
        self.scene.clear()

        # Reset the transformation of the view to ensure it starts from the original state
        self.ui.graphicsView.resetTransform()  # Reset transformations (zoom, pan)

        qimage = QImage(pil_image.tobytes(), pil_image.width, pil_image.height, pil_image.width * 3, QImage.Format_RGB888)
        # Load image
        # pixmap = QPixmap(image_path)
        pixmap = QPixmap(qimage)
        
        # Check if image is loaded successfully
        if pixmap.isNull():
            print(f"Failed to load image: {image_path}")
            return

        # Create pixmap item and add to scene
        pixmap_item = QGraphicsPixmapItem(pixmap)
        
        # Create pixmap item and add to scene
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(pixmap_item)
        
        # Adjust view to fit the image
        self.ui.graphicsView.setSceneRect(pixmap_item.boundingRect())
        self.ui.graphicsView.fitInView(pixmap_item.boundingRect(), Qt.KeepAspectRatio)
        self.originalScale = self.ui.graphicsView.transform().m11()
        
    def update_progress(self, value):
        """更新进度条的值"""
        self.ui.progressBar.setValue(value)
    
    def on_thread_finished(self):
        """线程完成后的回调"""
        if self.file_process_finished:
            return
        print("Thread finished")
        # NMS faces
        self.detector.nms_facearea()
        # 使用识别器进行识别
        self.recognizer.face_recognize(self.detector.boxes, self.image)
        rows = get_rows(self.recognizer.faces)
        row_names = get_row_names(self.recognizer.faces, rows)
        self.row_name = row_names
        # draw_name(self.image_result, row_names)
        draw_faces(self.image_result, self.recognizer.faces)
        # self.image_result.save(self.image_order_path)
        if self.ui.radioButton_order.isChecked():
            self.load_image(self.image_result)
        self.update_progress(100)

        self.set_ui_disabled(False)  # 重新启用控件
        # QApplication.restoreOverrideCursor()  # 恢复光标
        self.file_process_finished = True
    
    def set_ui_disabled(self, disable: bool):
        """禁用或启用界面控件"""
        # 禁用或启用整个窗口中的控件
        self.setDisabled(disable)
        # self.button_group.setDisabled(disable)  # 禁用开始按钮
        self.ui.file_button.setDisabled(disable)  # 禁用进度条
        self.ui.order_button.setDisabled(disable)  # 禁用状态标签
        self.ui.emotion_button.setDisabled(disable)  # 禁用状态标签
        self.ui.user_name.setDisabled(disable)  # 禁用状态标签
    
    def order(self):
        title_name = "排号信息"
        if self.row_name is None:
            return
        # 构造显示文本
        message_text = ""  # 初始化消息文本
        for index, row in enumerate(self.row_name, start=1):
            row_text = f"第{len(self.row_name) - index + 1}排: " + " ".join(row)  # 将该排的人名用空格连接起来
            message_text += row_text + "\n"  # 添加到最终的消息文本
        self.show_text(title_name, message_text)

    def show_text(self, title_name, message_text):
        # 创建自定义的对话框
        dialog = QDialog(self)
        dialog.setWindowTitle(title_name)
        dialog.setGeometry(150, 150, 400, 300)
        dialog.resize(800, 300)  # 设置大小为 400x300 像素

        # 创建文本框
        text_edit = QTextEdit(dialog)
        text_edit.setReadOnly(True)  # 设置为只读
        layout = QVBoxLayout(dialog)
        layout.addWidget(text_edit)

        # 设置文本框的内容
        text_edit.setText(message_text)

        # 显示对话框
        dialog.exec()
    
    def user_info(self):
        # 创建并显示消息框
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("这是一个弹出框显示的信息。")
    
    def extract_faces(self, img: Image, box) -> list:
        img = img.convert('RGB')
        #根据yolo检测人脸box扩大截图范围
        enlarged_face_img = get_enlarged_face_img(img, box, scale=3)
        #调用魔搭BSHM人像抠图
        img_output = portrait_matting(enlarged_face_img)
        result = img_output[OutputKeys.OUTPUT_IMG]
        #faces.append(result)
        #cv2图像通道BGR调整为RGB
        b, g, r, a = cv2.split(result)
        image_1 = cv2.merge([r, g, b, a])

        return image_1

    def emotion(self):
        if self.image_emotion is None:
            self.image_emotion = copy.deepcopy(self.image)
            #获取表情和闭眼状态
            self.set_ui_disabled(True)  # 禁用控件
            self.emotion_worker = Emotion_Worker(self.recognizer, self.eye_ratio)
            self.emotion_worker.progress.connect(self.update_progress)  # 连接信号到槽函数
            self.emotion_worker.finished.connect(self.emotion_thread_finished)  # 连接线程完成信号
            self.emotion_process_finished = False
            self.emotion_worker.start()
        else:
            self.show_emotion_info()

    def emotion_thread_finished(self):
        if self.emotion_process_finished:
            return
        self.image_emotion = draw_faces_emoji(self.image_emotion, self.recognizer.faces, self.emoji_dict)
        # self.image_emotion.save(self.image_emotion_path)
        if self.ui.radioButton_emotion.isChecked():
            self.load_image(self.image_emotion)
        self.set_ui_disabled(False)  # 重新启用控件
        # QApplication.restoreOverrideCursor()  # 恢复光标
        self.update_progress(100)
        self.emotion_process_finished = True
        self.emotion_worker.quit()
        self.show_emotion_info()

    def show_emotion_info(self):
        unhappy_count = 0
        close_count = 0
        # 构造显示文本
        message_text = "表情严肃: \n"  # 初始化消息文本

        for face in self.recognizer.faces:
            if 'unhappy' in face['emotion_state']:
                row_text = f"{face['name']} 严肃\n"
                message_text += row_text
                unhappy_count += 1
        
        message_text += "\n表情闭眼: \n"  # 初始化消息文本

        for face in self.recognizer.faces:
            if 'close' in face['emotion_state']:
                row_text = f"{face['name']} 闭眼\n"
                message_text += row_text
                close_count += 1

        message_text += f"\n表情严肃{unhappy_count}人，表情闭眼{close_count}人\n"  # 初始化消息文本
        self.show_text("表情识别结果", message_text)
# 程序入口
if __name__ == "__main__":
    # 初始化QApplication，界面展示要包含在QApplication初始化之后，结束之前
    app = QApplication(sys.argv)
 
    # 初始化并展示我们的界面组件
    window = MyWidget()
    window.show()
    
    # 结束QApplication
    sys.exit(app.exec())
