import gradio as gr
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
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWebEngineWidgets import QWebEngineView
# 导入我们生成的界面
from ui.main_ui import Ui_Dialog
import copy

facebank_path = 'images/MSE-p/个人'
facetest_path = 'images/MSE-p/f5dff87ed6c3d3dcf1ed44ae36aa83e.jpg'
face_detector = pipeline(Tasks.face_detection, model='gaosheng/face_detect')
# face_recognizer = pipeline(Tasks.face_recognition, model='damo/cv_ir101_facerecognition_cfglint')
face_recognizer = pipeline(Tasks.face_recognition, model='iic/cv_ir101_facerecognition_cfglint')
face_bank = load_face_bank(facebank_path, face_recognizer)

def inference(img: Image, draw_detect_enabled, detect_threshold, sim_threshold) -> json:
    boxes = detect(img, face_detector, draw_detect_enabled, detect_threshold)
    # img = resize_img(img)
    # img = img.convert('RGB') 
    # detection_result = face_detector(img)

    # boxes = np.array(detection_result[OutputKeys.BOXES])
    # scores = np.array(detection_result[OutputKeys.SCORES])
    
    faces = []
    for i in range(len(boxes)):
        box = boxes[i][:4]
        face_embedding = get_face_embedding(img, box, face_recognizer)
        name, sim = get_name_sim(face_embedding, face_bank)
        if name is None:
            continue
        if sim < sim_threshold:
            faces.append({'box': box, 'name': '未知', 'sim': sim})
        else:
            faces.append({'box': box, 'name': name, 'sim': sim})
    rows = get_rows(faces)
    row_names = get_row_names(faces, rows)
    draw_name(img, row_names)
    if draw_detect_enabled:
        draw_faces(img, faces)
    img.save('result.jpg')
    return img, get_row_names_text(row_names)

    # for i in range(len(boxes)):
    #     score = scores[i]
    #     if score < detect_threshold:
    #         continue
    #     box = boxes[i]
    #     face_embedding = get_face_embedding(img, box, face_recognizer)
    #     name, sim = get_name_sim(face_embedding, face_bank)
    #     if name is None:
    #         continue
    #     if sim < sim_threshold:
    #         faces.append({'box': box, 'name': '未知', 'sim': sim})
    #     else:
    #         faces.append({'box': box, 'name': name, 'sim': sim})
    # rows = get_rows(faces)
    # row_names = get_row_names(faces, rows)
    # draw_name(img, row_names)
    # if draw_detect_enabled:
    #     draw_faces(img, faces)
    # return img, get_row_names_text(row_names)

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

# 继承QWidget类，以获取其属性和方法
class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        # 设置界面为我们生成的界面
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.file_process_finished = False
        self.image_order_path = 'images/result.jpg'

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
        self.ui.checkBox.setChecked(True)
        self.ui.checkBox.stateChanged.connect(self.checkbox_changed)
        self.ui.order_button.clicked.connect(self.order)
        self.ui.emotion_button.clicked.connect(self.emotion)
        # 存储原始缩放级别
        self.originalScale = 1.0

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
            
            # 使用场景坐标进行后续处理
            print(f"Scene coordinates: {scenePos.x()}, {scenePos.y()}")

        elif event.button() == Qt.RightButton:
            # 处理右键点击事件
            self.resetViewScale()
            print("Right mouse button clicked")
        # 可以根据需要添加更多的事件处理

    def checkbox_changed(self):
        if self.ui.checkBox.isChecked():
            self.load_image(self.image_order_path)
        else:
            self.load_image(self.image_path)

    def search(self):
        # 获取输入框中的文本
        name = self.ui.user_name.text()
        
        for index, row in enumerate(self.row_name, start=1):
            row_num = len(self.row_name) - index + 1
            for col_num, name_i in enumerate(row, start=1):
                if name in name_i:
                    self.ui.user_info.setText(f"{name} is in row {row_num}, column {col_num}")
                    return

        self.ui.user_info.setText(f"{name} not found")
    
    def read_file_dialog(self):
        # 打开文件对话框，让用户选择文件
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Image Files (*.png *.jpg *.jpeg)")

        # 如果用户选择了文件，则显示文件路径
        if file_path:
            self.detector = detector(face_detector, 0.5)
            self.recognizer = recognizer(face_recognizer, face_bank, 0.3)
            self.image_path = file_path
            self.image = Image.open(file_path)
            self.load_image(file_path)
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
    
    def load_image(self, image_path):
        # Clear previous scene
        self.scene.clear()

        # Reset the transformation of the view to ensure it starts from the original state
        self.ui.graphicsView.resetTransform()  # Reset transformations (zoom, pan)

        # Load image
        pixmap = QPixmap(image_path)
        
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
        self.image_result.save(self.image_order_path)
        if self.ui.checkBox.isChecked():
            self.load_image(self.image_order_path)
        self.update_progress(100)

        self.set_ui_disabled(False)  # 重新启用控件
        # QApplication.restoreOverrideCursor()  # 恢复光标
        self.file_process_finished = True
    
    def set_ui_disabled(self, disable: bool):
        """禁用或启用界面控件"""
        # 禁用或启用整个窗口中的控件
        self.setDisabled(disable)
        self.ui.checkBox.setDisabled(disable)  # 禁用开始按钮
        self.ui.file_button.setDisabled(disable)  # 禁用进度条
        self.ui.order_button.setDisabled(disable)  # 禁用状态标签
        self.ui.emotion_button.setDisabled(disable)  # 禁用状态标签
        self.ui.user_name.setDisabled(disable)  # 禁用状态标签
    
    def order(self):
        # 创建自定义的对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("排号信息")
        dialog.setGeometry(150, 150, 400, 300)
        dialog.resize(800, 300)  # 设置大小为 400x300 像素

        # 创建文本框
        text_edit = QTextEdit(dialog)
        text_edit.setReadOnly(True)  # 设置为只读
        layout = QVBoxLayout(dialog)
        layout.addWidget(text_edit)

        if self.row_name is None:
            return
        # 构造显示文本
        message_text = ""  # 初始化消息文本
        for index, row in enumerate(self.row_name, start=1):
            row_text = f"第{len(self.row_name) - index + 1}排: " + " ".join(row)  # 将该排的人名用空格连接起来
            message_text += row_text + "\n"  # 添加到最终的消息文本

        # 设置文本框的内容
        text_edit.setText(message_text)

        # 显示对话框
        dialog.exec()
    
    def user_info(self):
        # 创建并显示消息框
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("这是一个弹出框显示的信息。")
    
    def emotion(self):
        # 获取输入框中的文本
        name = self.ui.user_name.text()

        # 在文本框中显示搜索结果
        self.ui.user_info.setText(f"Searching for {name}...")

    
# 程序入口
if __name__ == "__main__":
    # 初始化QApplication，界面展示要包含在QApplication初始化之后，结束之前
    app = QApplication(sys.argv)
 
    # 初始化并展示我们的界面组件
    window = MyWidget()
    window.show()
    
    # 结束QApplication
    sys.exit(app.exec())
