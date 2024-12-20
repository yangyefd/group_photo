# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QGraphicsView, QHBoxLayout,
    QLabel, QLayout, QLineEdit, QProgressBar,
    QPushButton, QRadioButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.setWindowModality(Qt.WindowModal)
        Dialog.resize(939, 648)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMaximumSize(QSize(939, 648))
        self.layoutWidget = QWidget(Dialog)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(9, 9, 97, 631))
        self.verticalLayout_4 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.file_button = QPushButton(self.layoutWidget)
        self.file_button.setObjectName(u"file_button")
        sizePolicy.setHeightForWidth(self.file_button.sizePolicy().hasHeightForWidth())
        self.file_button.setSizePolicy(sizePolicy)

        self.verticalLayout_4.addWidget(self.file_button)

        self.order_button = QPushButton(self.layoutWidget)
        self.order_button.setObjectName(u"order_button")
        sizePolicy.setHeightForWidth(self.order_button.sizePolicy().hasHeightForWidth())
        self.order_button.setSizePolicy(sizePolicy)

        self.verticalLayout_4.addWidget(self.order_button)

        self.emotion_button = QPushButton(self.layoutWidget)
        self.emotion_button.setObjectName(u"emotion_button")
        sizePolicy.setHeightForWidth(self.emotion_button.sizePolicy().hasHeightForWidth())
        self.emotion_button.setSizePolicy(sizePolicy)

        self.verticalLayout_4.addWidget(self.emotion_button)

        self.radioButton_ori = QRadioButton(self.layoutWidget)
        self.radioButton_ori.setObjectName(u"radioButton_ori")

        self.verticalLayout_4.addWidget(self.radioButton_ori)

        self.radioButton_order = QRadioButton(self.layoutWidget)
        self.radioButton_order.setObjectName(u"radioButton_order")

        self.verticalLayout_4.addWidget(self.radioButton_order)

        self.radioButton_emotion = QRadioButton(self.layoutWidget)
        self.radioButton_emotion.setObjectName(u"radioButton_emotion")

        self.verticalLayout_4.addWidget(self.radioButton_emotion)

        self.placeholder = QLabel(self.layoutWidget)
        self.placeholder.setObjectName(u"placeholder")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.placeholder.sizePolicy().hasHeightForWidth())
        self.placeholder.setSizePolicy(sizePolicy1)

        self.verticalLayout_4.addWidget(self.placeholder)

        self.layoutWidget1 = QWidget(Dialog)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(92, 9, 841, 631))
        self.verticalLayout = QVBoxLayout(self.layoutWidget1)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.graphicsView = QGraphicsView(self.layoutWidget1)
        self.graphicsView.setObjectName(u"graphicsView")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.graphicsView.sizePolicy().hasHeightForWidth())
        self.graphicsView.setSizePolicy(sizePolicy2)

        self.verticalLayout.addWidget(self.graphicsView)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.user_name = QLineEdit(self.layoutWidget1)
        self.user_name.setObjectName(u"user_name")
        sizePolicy.setHeightForWidth(self.user_name.sizePolicy().hasHeightForWidth())
        self.user_name.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.user_name)

        self.user_info = QLineEdit(self.layoutWidget1)
        self.user_info.setObjectName(u"user_info")

        self.horizontalLayout_2.addWidget(self.user_info)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.progressBar = QProgressBar(self.layoutWidget1)
        self.progressBar.setObjectName(u"progressBar")
        sizePolicy2.setHeightForWidth(self.progressBar.sizePolicy().hasHeightForWidth())
        self.progressBar.setSizePolicy(sizePolicy2)
        self.progressBar.setMaximumSize(QSize(16777215, 23))
        self.progressBar.setValue(0)

        self.verticalLayout.addWidget(self.progressBar)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"\u96c6\u4f53\u7167\u7cfb\u7edf", None))
        self.file_button.setText(QCoreApplication.translate("Dialog", u"\u6587\u4ef6", None))
        self.order_button.setText(QCoreApplication.translate("Dialog", u"\u6392\u53f7", None))
        self.emotion_button.setText(QCoreApplication.translate("Dialog", u"\u8868\u60c5", None))
        self.radioButton_ori.setText(QCoreApplication.translate("Dialog", u" \u539f\u56fe", None))
        self.radioButton_order.setText(QCoreApplication.translate("Dialog", u"\u68c0\u6d4b\u6846", None))
        self.radioButton_emotion.setText(QCoreApplication.translate("Dialog", u" \u8868\u60c5", None))
        self.placeholder.setText("")
    # retranslateUi

