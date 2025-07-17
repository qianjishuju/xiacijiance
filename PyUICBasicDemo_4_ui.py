# -*- coding: utf-8 -*-
import os
import sys
import threading
import time
import win32api
import win32con
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QLayout, \
    QApplication, QMainWindow
import configparser
from pynput import mouse, keyboard
from utlis import SerialThread
import chouse

config = configparser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'), encoding="utf-8")


class LoginDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("登录")
        self.username_label = QLabel("用户名:")
        self.username_input = QLineEdit("admin")
        self.password_label = QLabel("密码:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.authenticate)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def authenticate(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if username == config['Login']['Username'] and password == config['Login']['Password']:
            self.accept()
        else:
            QMessageBox.warning(self, "错误", "用户名或密码错误")


import serial.tools.list_ports


def get_serial_ports():
    # 获取可用的串口列表
    ports = list(serial.tools.list_ports.comports())
    # 提取每个串口的设备名称
    port_names = [port.device for port in ports]
    print(port_names)
    return port_names


# # 调用函数获取串口列表
# get_serial_ports()


class CustomTextEdit(QtWidgets.QTextEdit):
    linkClicked = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        anchor = self.anchorAt(event.pos())
        if anchor:
            self.linkClicked.emit(anchor)
        else:
            super().mousePressEvent(event)


class EnlargedWindow(QtWidgets.QDialog):
    def __init__(self, image):
        super(EnlargedWindow, self).__init__()

        self.setWindowTitle("Enlarged Image")
        self.setMinimumSize(600, 600)

        layout = QtWidgets.QVBoxLayout()

        label = QtWidgets.QLabel()
        label.setPixmap(QtGui.QPixmap.fromImage(image))
        label.setScaledContents(True)  # 设置自适应缩放
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)  # 设置大小策略
        layout.addWidget(label)

        self.setLayout(layout)


class Ui_MainWindow(object):
    def __init__(self):

        self.last_activity_time = None
        self.mode = None
        self.serial_thread = SerialThread()
        self.enlarged_window = None
        self.default_port = config.get('General', 'port')  # 串口
        self.default_baudrate = int(config.get('General', 'baudrate'))  # 路径
        self.keyboard_listener = None
        self.mouse_listener = None

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1068, 925)
        MainWindow.setLayoutDirection(QtCore.Qt.LeftToRight)
        MainWindow.setAutoFillBackground(True)

        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")

        self.horizontalLayout_14 = QtWidgets.QHBoxLayout(self.centralWidget)
        self.horizontalLayout_14.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_14.setSpacing(6)
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.tabWidget = QtWidgets.QTabWidget(self.centralWidget)
        self.tabWidget.setObjectName("tabWidget")

        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")

        self.horizontalLayout_13 = QtWidgets.QHBoxLayout(self.tab)
        self.horizontalLayout_13.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_13.setSpacing(6)
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout()
        self.verticalLayout_9.setSpacing(6)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.ComboDevices = QtWidgets.QComboBox(self.tab)
        self.ComboDevices.setObjectName("ComboDevices")
        self.verticalLayout_2.addWidget(self.ComboDevices)

        self.groupBox_3 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_3.setObjectName("groupBox_3")
        self.horizontalLayout_34 = QtWidgets.QHBoxLayout(self.groupBox_3)
        self.horizontalLayout_34.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_34.setSpacing(6)
        self.horizontalLayout_34.setObjectName("horizontalLayout_34")
        self.horizontalLayout_33 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_33.setSpacing(6)
        self.horizontalLayout_33.setObjectName("horizontalLayout_33")
        self.groupBox_11 = QtWidgets.QGroupBox(self.groupBox_3)
        self.groupBox_11.setObjectName("groupBox_11")
        self.horizontalLayout_28 = QtWidgets.QHBoxLayout(self.groupBox_11)
        self.horizontalLayout_28.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_28.setSpacing(6)
        self.horizontalLayout_28.setObjectName("horizontalLayout_28")

        self.widgetDisplay = QtWidgets.QLabel(self.groupBox_11)
        self.widgetDisplay.setText("")
        self.widgetDisplay.setObjectName("widgetDisplay")
        self.widgetDisplay.setAlignment(Qt.AlignCenter)
        self.widgetDisplay.setScaledContents(True)  # 设置内容自适应缩放
        self.widgetDisplay.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))

        self.horizontalLayout_28.addWidget(self.widgetDisplay)

        self.horizontalLayout_33.addWidget(self.groupBox_11)
        self.verticalLayout_14 = QtWidgets.QVBoxLayout()
        self.verticalLayout_14.setSpacing(6)
        self.verticalLayout_14.setObjectName("verticalLayout_14")
        self.groupBox_9 = QtWidgets.QGroupBox(self.groupBox_3)
        self.groupBox_9.setObjectName("groupBox_9")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout(self.groupBox_9)
        self.horizontalLayout_10.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_10.setSpacing(6)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_13 = QtWidgets.QLabel(self.groupBox_9)
        self.label_13.setText("")
        self.label_13.setObjectName("label_13")
        self.horizontalLayout_10.addWidget(self.label_13)
        self.verticalLayout_14.addWidget(self.groupBox_9)
        self.groupBox_10 = QtWidgets.QGroupBox(self.groupBox_3)
        self.groupBox_10.setObjectName("groupBox_10")
        self.horizontalLayout_27 = QtWidgets.QHBoxLayout(self.groupBox_10)
        self.horizontalLayout_27.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_27.setSpacing(6)
        self.horizontalLayout_27.setObjectName("horizontalLayout_27")
        self.label_14 = QtWidgets.QLabel(self.groupBox_10)
        self.label_14.setText("")
        self.label_14.setObjectName("label_14")
        self.horizontalLayout_27.addWidget(self.label_14)
        self.verticalLayout_14.addWidget(self.groupBox_10)
        self.horizontalLayout_33.addLayout(self.verticalLayout_14)
        self.horizontalLayout_33.setStretch(0, 5)
        self.horizontalLayout_33.setStretch(1, 3)
        self.horizontalLayout_34.addLayout(self.horizontalLayout_33)
        self.verticalLayout_2.addWidget(self.groupBox_3)
        self.verticalLayout_9.addLayout(self.verticalLayout_2)

        self.groupBox_2 = QtWidgets.QGroupBox(self.tab)
        self.groupBox_2.setObjectName("groupBox_2")
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_11.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_11.setSpacing(6)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")

        self.text_display = QtWidgets.QTextBrowser(self.groupBox_2)

        # self.text_display.setMinimumSize(QtCore.QSize(0, 531))
        self.text_display.setObjectName("text_display")
        self.horizontalLayout_11.addWidget(self.text_display)
        self.verticalLayout_9.addWidget(self.groupBox_2)
        self.verticalLayout_9.setStretch(0, 9)
        self.verticalLayout_9.setStretch(1, 3)
        self.horizontalLayout_13.addLayout(self.verticalLayout_9)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout(self.tab_2)
        self.horizontalLayout_12.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_12.setSpacing(6)
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout()
        self.verticalLayout_10.setSpacing(6)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.buttonx = QtWidgets.QPushButton(self.tab_2)
        self.buttonx.setObjectName("buttonx")
        self.buttonx.setCheckable(True)
        self.buttonx.setMaximumSize(QtCore.QSize(100, 23))
        self.buttonx.setGeometry(QtCore.QRect(10, 0, 101, 31))
        self.buttonx.clicked.connect(self.toggleMode)
        self.verticalLayout_10.addWidget(self.buttonx)
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setSpacing(6)
        self.verticalLayout_8.setObjectName("verticalLayout_8")

        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.groupInit = QtWidgets.QGroupBox(self.tab_2)
        self.groupInit.setObjectName("groupInit")
        self.horizontalLayout_19 = QtWidgets.QHBoxLayout(self.groupInit)
        self.horizontalLayout_19.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_19.setSpacing(6)
        self.horizontalLayout_19.setObjectName("horizontalLayout_19")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName("gridLayout")
        self.bnClose = QtWidgets.QPushButton(self.groupInit)
        self.bnClose.setEnabled(False)
        self.bnClose.setObjectName("bnClose")
        self.gridLayout.addWidget(self.bnClose, 2, 2, 1, 1)
        self.bnOpen = QtWidgets.QPushButton(self.groupInit)
        self.bnOpen.setObjectName("bnOpen")
        self.gridLayout.addWidget(self.bnOpen, 2, 1, 1, 1)
        self.bnEnum = QtWidgets.QPushButton(self.groupInit)
        self.bnEnum.setObjectName("bnEnum")
        self.gridLayout.addWidget(self.bnEnum, 1, 1, 1, 2)
        self.horizontalLayout_19.addLayout(self.gridLayout)
        self.horizontalLayout_4.addWidget(self.groupInit)
        self.groupBox = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox.setObjectName("groupBox")
        self.horizontalLayout_16 = QtWidgets.QHBoxLayout(self.groupBox)
        self.horizontalLayout_16.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_16.setSpacing(6)
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setSpacing(6)
        self.gridLayout_4.setObjectName("gridLayout_4")

        self.double_spin_box = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.double_spin_box.setRange(0.1, 1)
        self.double_spin_box.setSingleStep(0.1)
        self.double_spin_box.setDecimals(2)

        self.gridLayout_4.addWidget(self.double_spin_box, 2, 1, 1, 2)

        # 检测阈值
        self.bnEnum_3 = QtWidgets.QPushButton(self.groupBox)
        self.bnEnum_3.setObjectName("bnEnum_3")
        self.gridLayout_4.addWidget(self.bnEnum_3, 1, 1, 1, 2)
        self.horizontalLayout_16.addLayout(self.gridLayout_4)

        self.horizontalLayout_4.addWidget(self.groupBox)
        self.verticalLayout_3.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setSpacing(6)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.groupParam = QtWidgets.QGroupBox(self.tab_2)
        self.groupParam.setEnabled(False)
        self.groupParam.setObjectName("groupParam")
        self.horizontalLayout_18 = QtWidgets.QHBoxLayout(self.groupParam)
        self.horizontalLayout_18.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_18.setSpacing(6)
        self.horizontalLayout_18.setObjectName("horizontalLayout_18")
        self.gridLayoutParam = QtWidgets.QGridLayout()
        self.gridLayoutParam.setSpacing(6)
        self.gridLayoutParam.setObjectName("gridLayoutParam")
        self.label_6 = QtWidgets.QLabel(self.groupParam)
        self.label_6.setObjectName("label_6")
        self.gridLayoutParam.addWidget(self.label_6, 3, 0, 1, 1)
        self.edtGain = QtWidgets.QLineEdit(self.groupParam)
        self.edtGain.setObjectName("edtGain")
        self.gridLayoutParam.addWidget(self.edtGain, 1, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.groupParam)
        self.label_5.setObjectName("label_5")
        self.gridLayoutParam.addWidget(self.label_5, 1, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.groupParam)
        self.label_4.setObjectName("label_4")
        self.gridLayoutParam.addWidget(self.label_4, 0, 0, 1, 1)
        self.edtExposureTime = QtWidgets.QLineEdit(self.groupParam)
        self.edtExposureTime.setObjectName("edtExposureTime")
        self.gridLayoutParam.addWidget(self.edtExposureTime, 0, 1, 1, 1)
        self.bnGetParam = QtWidgets.QPushButton(self.groupParam)
        self.bnGetParam.setObjectName("bnGetParam")
        self.gridLayoutParam.addWidget(self.bnGetParam, 4, 0, 1, 1)
        self.bnSetParam = QtWidgets.QPushButton(self.groupParam)
        self.bnSetParam.setObjectName("bnSetParam")
        self.gridLayoutParam.addWidget(self.bnSetParam, 4, 1, 1, 1)
        self.edtFrameRate = QtWidgets.QLineEdit(self.groupParam)
        self.edtFrameRate.setObjectName("edtFrameRate")
        self.gridLayoutParam.addWidget(self.edtFrameRate, 3, 1, 1, 1)
        self.gridLayoutParam.setColumnStretch(0, 2)
        self.gridLayoutParam.setColumnStretch(1, 3)
        self.horizontalLayout_18.addLayout(self.gridLayoutParam)
        self.horizontalLayout_5.addWidget(self.groupParam)
        self.groupGrab = QtWidgets.QGroupBox(self.tab_2)
        self.groupGrab.setEnabled(False)
        self.groupGrab.setObjectName("groupGrab")
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout(self.groupGrab)
        self.horizontalLayout_15.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_15.setSpacing(6)
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setSpacing(6)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.bnSaveImage = QtWidgets.QPushButton(self.groupGrab)
        self.bnSaveImage.setEnabled(False)
        self.bnSaveImage.setObjectName("bnSaveImage")
        self.gridLayout_2.addWidget(self.bnSaveImage, 4, 0, 1, 2)
        self.radioContinueMode = QtWidgets.QRadioButton(self.groupGrab)
        self.radioContinueMode.setObjectName("radioContinueMode")
        self.gridLayout_2.addWidget(self.radioContinueMode, 0, 0, 1, 1)
        self.radioTriggerMode = QtWidgets.QRadioButton(self.groupGrab)
        self.radioTriggerMode.setObjectName("radioTriggerMode")
        self.gridLayout_2.addWidget(self.radioTriggerMode, 0, 1, 1, 1)
        self.bnStop = QtWidgets.QPushButton(self.groupGrab)
        self.bnStop.setEnabled(False)
        self.bnStop.setObjectName("bnStop")
        self.gridLayout_2.addWidget(self.bnStop, 2, 1, 1, 1)
        self.bnStart = QtWidgets.QPushButton(self.groupGrab)
        self.bnStart.setEnabled(False)
        self.bnStart.setObjectName("bnStart")
        self.gridLayout_2.addWidget(self.bnStart, 2, 0, 1, 1)
        self.bnSoftwareTrigger = QtWidgets.QPushButton(self.groupGrab)
        self.bnSoftwareTrigger.setEnabled(False)
        self.bnSoftwareTrigger.setObjectName("bnSoftwareTrigger")
        self.gridLayout_2.addWidget(self.bnSoftwareTrigger, 3, 0, 1, 2)
        self.horizontalLayout_15.addLayout(self.gridLayout_2)
        self.horizontalLayout_5.addWidget(self.groupGrab)
        self.horizontalLayout_5.setStretch(0, 1)
        self.horizontalLayout_5.setStretch(1, 1)
        self.verticalLayout_3.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setSpacing(6)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.groupInit_2 = QtWidgets.QGroupBox(self.tab_2)
        self.groupInit_2.setObjectName("groupInit_2")
        self.horizontalLayout_17 = QtWidgets.QHBoxLayout(self.groupInit_2)
        self.horizontalLayout_17.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_17.setSpacing(6)
        self.horizontalLayout_17.setObjectName("horizontalLayout_17")
        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setSpacing(6)
        self.gridLayout_3.setObjectName("gridLayout_3")

        # 串口通讯
        self.button1 = QtWidgets.QPushButton(self.groupInit_2)
        self.button1.setObjectName("bnEnum_2")
        self.button1.clicked.connect(self.on_button1_clicked)

        self.gridLayout_3.addWidget(self.button1, 1, 1, 1, 2)

        self.input1 = QtWidgets.QComboBox(self.groupInit_2)
        self.input1.setObjectName("comboBox")
        self.input1.addItems(get_serial_ports())
        self.input1.setCurrentText(self.default_port)  # 设置默认端口
        # 创建输入框2################################
        self.gridLayout_3.addWidget(self.input1, 2, 1, 1, 1)
        self.input2 = QtWidgets.QComboBox(self.groupInit_2)
        self.input2.setObjectName("comboBox_2")
        self.input2.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.input2.setCurrentText(str(self.default_baudrate))  # 设置默认波特率
        self.gridLayout_3.addWidget(self.input2, 2, 2, 1, 1)

        self.horizontalLayout_17.addLayout(self.gridLayout_3)
        self.horizontalLayout_6.addWidget(self.groupInit_2)
        self.groupInit_3 = QtWidgets.QGroupBox(self.tab_2)
        self.groupInit_3.setObjectName("groupInit_3")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.groupInit_3)
        self.verticalLayout_11.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_11.setSpacing(6)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.gridLayout_6 = QtWidgets.QGridLayout()
        self.gridLayout_6.setSpacing(6)
        self.gridLayout_6.setObjectName("gridLayout_6")

        self.lineEdit = QtWidgets.QLineEdit(self.groupInit_3)
        self.lineEdit.setObjectName("lineEdit")
        self.gridLayout_6.addWidget(self.lineEdit, 2, 2, 1, 1)

        self.select_folder_button = QtWidgets.QPushButton(self.groupInit_3)
        self.select_folder_button.setObjectName("bnEnum_4")
        self.gridLayout_6.addWidget(self.select_folder_button, 1, 2, 1, 1)
        self.select_folder_button.clicked.connect(self.on_select_folder_button_clicked)
        self.verticalLayout_11.addLayout(self.gridLayout_6)

        self.horizontalLayout_6.addWidget(self.groupInit_3)
        self.horizontalLayout_6.setStretch(0, 1)
        self.horizontalLayout_6.setStretch(1, 1)
        self.verticalLayout_3.addLayout(self.horizontalLayout_6)
        self.groupBox_4 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.label = QtWidgets.QLabel(self.groupBox_4)
        self.label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.label_2 = QtWidgets.QLabel(self.groupBox_4)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.label_3 = QtWidgets.QLabel(self.groupBox_4)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.label_7 = QtWidgets.QLabel(self.groupBox_4)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout.addWidget(self.label_7)
        self.label_8 = QtWidgets.QLabel(self.groupBox_4)
        self.label_8.setObjectName("label_8")

        self.horizontalLayout.addWidget(self.label_8)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)
        self.horizontalLayout.setStretch(2, 1)
        self.horizontalLayout.setStretch(3, 1)
        self.horizontalLayout.setStretch(4, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(0, 0, -1, 0)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        self.minDist_1 = QtWidgets.QLineEdit(self.groupBox_4)
        self.minDist_1.setObjectName("minDist_1")
        self.horizontalLayout_2.addWidget(self.minDist_1)
        self.param1_1 = QtWidgets.QLineEdit(self.groupBox_4)
        self.param1_1.setObjectName("param1_1")
        self.horizontalLayout_2.addWidget(self.param1_1)
        self.param2_1 = QtWidgets.QLineEdit(self.groupBox_4)
        self.param2_1.setObjectName("param2_1")
        self.horizontalLayout_2.addWidget(self.param2_1)
        self.minRadius_1 = QtWidgets.QLineEdit(self.groupBox_4)
        self.minRadius_1.setObjectName("minRadius_1")
        self.horizontalLayout_2.addWidget(self.minRadius_1)
        self.maxRadius_1 = QtWidgets.QLineEdit(self.groupBox_4)
        self.maxRadius_1.setObjectName("maxRadius_1")
        self.horizontalLayout_2.addWidget(self.maxRadius_1)
        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 1)
        self.horizontalLayout_2.setStretch(2, 1)
        self.horizontalLayout_2.setStretch(3, 1)
        self.horizontalLayout_2.setStretch(4, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_3.addWidget(self.groupBox_4)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setSpacing(6)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.groupBox_5 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_5.setObjectName("groupBox_5")
        self.horizontalLayout_20 = QtWidgets.QHBoxLayout(self.groupBox_5)
        self.horizontalLayout_20.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_20.setSpacing(6)
        self.horizontalLayout_20.setObjectName("horizontalLayout_20")

        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")

        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setObjectName("verticalLayout_4")

        self.label_9 = QtWidgets.QLabel(self.groupBox_5)
        self.label_9.setObjectName("label_9")
        self.verticalLayout_4.addWidget(self.label_9)
        self.ksize = QtWidgets.QLineEdit(self.groupBox_5)
        self.ksize.setMouseTracking(True)
        self.ksize.setObjectName("ksize")

        self.verticalLayout_4.addWidget(self.ksize)
        self.horizontalLayout_3.addLayout(self.verticalLayout_4)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_11 = QtWidgets.QLabel(self.groupBox_5)
        self.label_11.setObjectName("label_11")
        self.verticalLayout_5.addWidget(self.label_11)
        self.ksize_3 = QtWidgets.QLineEdit(self.groupBox_5)
        self.ksize_3.setMouseTracking(True)
        self.ksize_3.setObjectName("ksize_3")
        self.verticalLayout_5.addWidget(self.ksize_3)
        self.horizontalLayout_3.addLayout(self.verticalLayout_5)

        self.horizontalLayout_20.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_7.addWidget(self.groupBox_5)

        self.groupBox_7 = QtWidgets.QGroupBox(self.tab_2)
        self.groupBox_7.setObjectName("groupBox_7")

        self.widget = QtWidgets.QWidget(self.groupBox_7)
        self.widget.setGeometry(QtCore.QRect(11, 23, 102, 50))
        self.widget.setObjectName("widget")

        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_7.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_7.setSpacing(6)
        self.verticalLayout_7.setObjectName("verticalLayout_7")

        yanshix = self.duqu_yanshi_config()
        self.yanshi = QtWidgets.QDoubleSpinBox(self.widget)
        self.yanshi.setMinimumSize(QtCore.QSize(100, 23))
        self.yanshi.setMaximumSize(QtCore.QSize(100, 23))
        self.yanshi.setRange(0.1, 10)
        self.yanshi.setSingleStep(0.1)
        self.yanshi.setDecimals(1)
        self.yanshi.setValue(yanshix)
        self.yanshi.setObjectName("lineEdit_2")
        self.verticalLayout_7.addWidget(self.yanshi)

        self.horizontalLayout_7.addWidget(self.groupBox_7)

        self.horizontalLayout_7.setStretch(0, 3)
        self.horizontalLayout_7.setStretch(1, 1)
        self.horizontalLayout_7.setStretch(2, 1)
        self.verticalLayout_3.addLayout(self.horizontalLayout_7)

        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setSpacing(6)

        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label_12 = QtWidgets.QLabel(self.tab_2)
        self.label_12.setObjectName("label_12")
        self.verticalLayout_6.addWidget(self.label_12)

        self.pushButton_2 = QtWidgets.QPushButton(self.tab_2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_2.clicked.connect(self.write_config_file)
        self.verticalLayout_6.addWidget(self.pushButton_2)

        self.verticalLayout_3.addLayout(self.verticalLayout_6)
        self.verticalLayout_3.setStretch(0, 2)
        self.verticalLayout_3.setStretch(1, 2)
        self.verticalLayout_3.setStretch(2, 2)
        self.verticalLayout_3.setStretch(3, 2)
        self.verticalLayout_3.setStretch(4, 2)
        self.verticalLayout_8.addLayout(self.verticalLayout_3)

        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setSpacing(6)
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.horizontalLayout_21 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_21.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.horizontalLayout_21.setContentsMargins(100, -1, -1, -1)
        self.horizontalLayout_21.setSpacing(6)
        self.horizontalLayout_21.setObjectName("horizontalLayout_21")
        self.horizontalLayout_8.addLayout(self.horizontalLayout_21)

        self.widgetDisplay1 = QtWidgets.QLabel(self.tab_2)
        self.widgetDisplay1.setMinimumSize(QtCore.QSize(119, 119))
        self.widgetDisplay1.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.widgetDisplay1.setObjectName("widgetDisplay1")
        self.widgetDisplay1.setAlignment(Qt.AlignCenter)
        self.widgetDisplay1.setScaledContents(True)  # 设置自适应缩放
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.widgetDisplay1.setSizePolicy(size_policy)
        self.horizontalLayout_8.addWidget(self.widgetDisplay1)

        self.horizontalLayout_8.setStretch(0, 7)
        self.horizontalLayout_8.setStretch(1, 1)
        self.verticalLayout_8.addLayout(self.horizontalLayout_8)
        self.verticalLayout_8.setStretch(0, 1)
        self.verticalLayout_10.addLayout(self.verticalLayout_8)
        self.horizontalLayout_12.addLayout(self.verticalLayout_10)
        self.tabWidget.addTab(self.tab_2, "")

        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")

        self.groupBox_8 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_8.setGeometry(QtCore.QRect(350, 50, 350, 171))
        self.groupBox_8.setObjectName("groupBox_8")

        self.verticalLayout_13 = QtWidgets.QVBoxLayout(self.groupBox_8)
        self.verticalLayout_13.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_13.setSpacing(6)
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.horizontalLayout_29 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_29.setSpacing(6)
        self.horizontalLayout_29.setObjectName("horizontalLayout_29")
        self.verticalLayout_13.addLayout(self.horizontalLayout_29)
        self.horizontalLayout_30 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_30.setSpacing(6)
        self.horizontalLayout_30.setObjectName("horizontalLayout_30")
        self.bnEnum_11 = QtWidgets.QPushButton(self.groupBox_8)
        self.bnEnum_11.setObjectName("bnEnum_11")
        self.horizontalLayout_30.addWidget(self.bnEnum_11)
        self.lineEdit_10 = QtWidgets.QLineEdit(self.groupBox_8)
        self.lineEdit_10.setObjectName("lineEdit_10")
        self.horizontalLayout_30.addWidget(self.lineEdit_10)
        self.verticalLayout_13.addLayout(self.horizontalLayout_30)
        self.horizontalLayout_31 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_31.setSpacing(6)
        self.horizontalLayout_31.setObjectName("horizontalLayout_31")
        self.bnEnum_12 = QtWidgets.QPushButton(self.groupBox_8)
        self.bnEnum_12.setObjectName("bnEnum_12")
        self.horizontalLayout_31.addWidget(self.bnEnum_12)
        self.lineEdit_11 = QtWidgets.QLineEdit(self.groupBox_8)
        self.lineEdit_11.setObjectName("lineEdit_11")
        self.horizontalLayout_31.addWidget(self.lineEdit_11)
        self.verticalLayout_13.addLayout(self.horizontalLayout_31)
        self.horizontalLayout_32 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_32.setSpacing(6)
        self.horizontalLayout_32.setObjectName("horizontalLayout_32")
        self.bnEnum_13 = QtWidgets.QPushButton(self.groupBox_8)
        self.bnEnum_13.setObjectName("bnEnum_13")
        self.horizontalLayout_32.addWidget(self.bnEnum_13)
        self.lineEdit_12 = QtWidgets.QLineEdit(self.groupBox_8)
        self.lineEdit_12.setObjectName("lineEdit_12")
        self.horizontalLayout_32.addWidget(self.lineEdit_12)
        self.lineEdit_13 = QtWidgets.QLineEdit(self.groupBox_8)
        self.lineEdit_13.setObjectName("lineEdit_13")
        self.horizontalLayout_32.addWidget(self.lineEdit_13)
        self.verticalLayout_13.addLayout(self.horizontalLayout_32)
        self.test_3 = QtWidgets.QPushButton(self.groupBox_8)
        self.test_3.setObjectName("test_3")
        self.test_3.clicked.connect(self.write_config_file)

        self.verticalLayout_13.addWidget(self.test_3)

        self.groupBox_6 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_6.setGeometry(QtCore.QRect(1, 50, 350, 171))
        self.groupBox_6.setObjectName("groupBox_6")

        self.verticalLayout_12 = QtWidgets.QVBoxLayout(self.groupBox_6)
        self.verticalLayout_12.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_12.setSpacing(6)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setSpacing(6)
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")

        self.test = QtWidgets.QPushButton(self.widget)
        self.test.setObjectName("test")
        self.test.clicked.connect(self.open_color_picker)

        self.horizontalLayout_9.addWidget(self.test)
        self.verticalLayout_12.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_24 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_24.setSpacing(6)
        self.horizontalLayout_24.setObjectName("horizontalLayout_24")

        self.bnEnum_7 = QtWidgets.QPushButton(self.groupBox_6)
        self.bnEnum_7.setObjectName("bnEnum_5")
        # ##########################################
        self.bnEnum_7.clicked.connect(self.select_tiejiao_file)

        self.horizontalLayout_24.addWidget(self.bnEnum_7)
        self.lineEdit_6 = QtWidgets.QLineEdit(self.groupBox_6)
        self.lineEdit_6.setObjectName("lineEdit_6")
        self.horizontalLayout_24.addWidget(self.lineEdit_6)
        self.verticalLayout_12.addLayout(self.horizontalLayout_24)

        self.horizontalLayout_23 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_23.setSpacing(6)
        self.horizontalLayout_23.setObjectName("horizontalLayout_23")
        self.bnEnum_6 = QtWidgets.QPushButton(self.groupBox_6)
        self.bnEnum_6.setObjectName("bnEnum_5")
        # #########################################
        self.bnEnum_6.clicked.connect(self.select_yuan_file)

        self.horizontalLayout_23.addWidget(self.bnEnum_6)
        self.lineEdit_5 = QtWidgets.QLineEdit(self.groupBox_6)
        self.lineEdit_5.setObjectName("lineEdit_5")
        self.horizontalLayout_23.addWidget(self.lineEdit_5)
        self.verticalLayout_12.addLayout(self.horizontalLayout_23)

        self.horizontalLayout_22 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_22.setSpacing(6)
        self.horizontalLayout_22.setObjectName("horizontalLayout_22")

        self.bnEnum_5 = QtWidgets.QPushButton(self.groupBox_6)
        self.bnEnum_5.setObjectName("bnEnum_5")
        # ###############################################
        self.bnEnum_5.clicked.connect(self.select_h5_file)

        self.horizontalLayout_22.addWidget(self.bnEnum_5)
        self.lineEdit_3 = QtWidgets.QLineEdit(self.groupBox_6)
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.horizontalLayout_22.addWidget(self.lineEdit_3)

        self.verticalLayout_12.addLayout(self.horizontalLayout_22)

        self.pushButton_4 = QtWidgets.QPushButton(self.tab_3)
        self.pushButton_4.setGeometry(QtCore.QRect(10, 10, 100, 23))
        self.pushButton_4.setMaximumSize(QtCore.QSize(100, 23))
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_4.clicked.connect(self.toggleMode)

        self.tabWidget.addTab(self.tab_3, "")

        self.horizontalLayout_14.addWidget(self.tabWidget)
        MainWindow.setCentralWidget(self.centralWidget)
        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1068, 23))
        self.menuBar.setObjectName("menuBar")
        self.menu = QtWidgets.QMenu(self.menuBar)
        self.menu.setObjectName("menu")
        MainWindow.setMenuBar(self.menuBar)
        self.actioninstructions = QtWidgets.QAction(MainWindow)
        self.actioninstructions.setObjectName("actioninstructions")
        self.menu.addAction(self.actioninstructions)
        self.menuBar.addAction(self.menu.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.on_button1_clicked()  # 开机自动连接串口
        self.image_folder_path()
        self.set_layout_widgets_enabled(self.verticalLayout_3, False)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBox_3.setTitle(_translate("MainWindow", "视频显示区域"))
        self.groupBox_9.setTitle(_translate("MainWindow", "贴胶"))
        self.groupBox_10.setTitle(_translate("MainWindow", "圆查找"))
        self.groupBox_2.setTitle(_translate("MainWindow", "文本显示"))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "显示区域"))

        self.groupInit.setTitle(_translate("MainWindow", "初始化"))
        self.bnClose.setText(_translate("MainWindow", "关闭设备"))
        self.bnOpen.setText(_translate("MainWindow", "打开设备"))
        self.bnEnum.setText(_translate("MainWindow", "查找设备"))
        self.groupBox.setTitle(_translate("MainWindow", "阀值"))
        self.bnEnum_3.setText(_translate("MainWindow", "设置阀值"))
        self.groupParam.setTitle(_translate("MainWindow", "参数"))
        self.label_6.setText(_translate("MainWindow", "帧率"))
        self.edtGain.setText(_translate("MainWindow", "0"))
        self.label_5.setText(_translate("MainWindow", "增益"))
        self.label_4.setText(_translate("MainWindow", "曝光"))
        self.edtExposureTime.setText(_translate("MainWindow", "0"))
        self.bnGetParam.setText(_translate("MainWindow", "获取参数"))
        self.bnSetParam.setText(_translate("MainWindow", "设置参数"))
        self.edtFrameRate.setText(_translate("MainWindow", "0"))
        self.groupGrab.setTitle(_translate("MainWindow", "采集"))
        self.bnSaveImage.setText(_translate("MainWindow", "保存图像"))
        self.radioContinueMode.setText(_translate("MainWindow", "连续模式"))
        self.radioTriggerMode.setText(_translate("MainWindow", "触发模式"))
        self.bnStop.setText(_translate("MainWindow", "停止采集"))
        self.bnStart.setText(_translate("MainWindow", "开始采集"))
        self.bnSoftwareTrigger.setText(_translate("MainWindow", "软触发一次"))
        self.groupInit_2.setTitle(_translate("MainWindow", "串口"))
        self.button1.setText(_translate("MainWindow", "串口设置"))
        self.groupInit_3.setTitle(_translate("MainWindow", "图片存放路径"))
        self.select_folder_button.setText(_translate("MainWindow", "选择路径"))
        self.groupBox_4.setTitle(_translate("MainWindow", "圆阈值"))
        self.label_11.setText(
            _translate("MainWindow", "<html><head/><body><p align=\"center\"> 操作延时(MS)</p></body></html>"))
        self.pushButton_2.setText(_translate("MainWindow", "保存"))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "参数设置"))

        self.groupBox_7.setTitle(_translate("MainWindow", "延时"))
        self.groupBox_6.setTitle(_translate("MainWindow", "工具"))
        self.test.setText(_translate("MainWindow", "抽色工具"))
        self.bnEnum_5.setText(_translate("MainWindow", "异物检测算法路径"))
        self.bnEnum_6.setText(_translate("MainWindow", "圆检测算法路径  "))
        self.bnEnum_7.setText(_translate("MainWindow", "贴膜识别算法路径"))

        self.groupBox_8.setTitle(_translate("MainWindow", "算法参数"))
        # self.bnEnum_11.setText(_translate("MainWindow", "贴膜识别算法阈值"))
        self.bnEnum_12.setText(_translate("MainWindow", "异物检测算法阈值"))
        self.bnEnum_13.setText(_translate("MainWindow", "异物检测算法阈值"))
        self.test_3.setText(_translate("MainWindow", "保存参数"))

        self.buttonx.setText(_translate("MainWindow", "生产模式"))
        self.pushButton_4.setText(_translate("MainWindow", "生产模式"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("MainWindow", "参数二"))
        self.menu.setTitle(_translate("MainWindow", "帮助"))
        self.actioninstructions.setText(_translate("MainWindow", "说明"))
        self.lineEdit.setText(config.get("folder_path", "default_folder"))
        self.lineEdit_3.setText(config.get("folder_path", "yiwu_model"))
        self.lineEdit_5.setText(config.get("folder_path", "yuan_model"))
        self.lineEdit_6.setText(config.get("folder_path", "tiejiao_model"))
        self.lineEdit_11.setText(config.get('threshold', 'len_result'))
        self.lineEdit_12.setText(config.get('threshold', 'max_value'))
        self.lineEdit_13.setText(config.get('threshold', 'sum_result'))
        self.ksize_3.setText(config.get('size', 'caozuoyanshi'))

    def select_file_and_update_config(self, line_edit, config_key):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog  # 確保使用 PyQt 的文件對話框
        fileName, _ = QFileDialog.getOpenFileName(self.centralWidget, "Select .pth File", "",
                                                  "PyTorch Files (*.pth);;All Files (*)",
                                                  options=options)
        if fileName:
            line_edit.setText(fileName)
            fileName = fileName.replace('\\', '/')
            config.set("folder_path", config_key, fileName)
            self.save_config()
            print(f'Selected file: {fileName}')

    def save_config(self):
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'), 'w',
                  encoding='utf-8') as configfile:
            config.write(configfile)

    def select_h5_file(self):
        self.select_file_and_update_config(self.lineEdit_3, "yiwu_model")

    def select_yuan_file(self):
        self.select_file_and_update_config(self.lineEdit_5, "yuan_model")

    def select_tiejiao_file(self):
        self.select_file_and_update_config(self.lineEdit_6, "tiejiao_model")

    def open_color_picker(self):
        self.color_picker_window = chouse.ColorPicker()
        self.color_picker_window.show()

    def on_select_folder_button_clicked(self):
        folder = QFileDialog.getExistingDirectory(self.centralWidget, '选择文件夹')
        try:
            if folder:
                self.lineEdit.setText(folder)
                self.save_folder_to_file(folder)
                folder = folder.replace('/', '\\')
                self.text_display.append(f"图片保存路径是：{folder}")

        except Exception as e:
            # 处理异常情况
            print(f"选择文件夹时发生错误: {str(e)}")
            self.text_display.append(f"选择文件夹时发生错误: {str(e)}")

    def image_folder_path(self):
        try:
            self.default_folder = config.get('folder_path', 'default_folder')
            self.windows_path = os.path.abspath(self.default_folder).replace('/', '\\')
            self.text_display.append(f"图片保存路径是{self.windows_path}")

        except Exception as e:
            self.text_display.append(f"文件路径读取错误: {e}")

    @staticmethod
    def save_folder_to_file(folder_path):
        if not config.has_section('folder_path'):
            config.add_section('folder_path')
        config.set('folder_path', 'default_folder', folder_path)
        # 创建一个临时文件
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'), 'w',
                  encoding='utf-8') as configfile:
            config.write(configfile)

    def on_button1_clicked(self):
        def connect_serial(port, baudrate):
            if self.serial_thread.start_serial(port, baudrate):
                self.text_display.append(f"串口1连接成功 {port} 波特率 {baudrate}")
                config = QSettings(
                    os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'),
                    QSettings.IniFormat
                )
                config.setIniCodec('UTF-8')
                config.setValue("port", port)
                config.setValue("baudrate", baudrate)
                self.button1.setText("更改串口")
                return True
            else:
                self.text_display.append(f"串口1连接不成功 {port} 波特率 {baudrate}")
                return False

        def close_and_reconnect():
            self.serial_thread.stop_serial()
            port = self.input1.currentText()
            baudrate = int(self.input2.currentText())
            connect_serial(port, baudrate)

        port = self.input1.currentText()
        baudrate = int(self.input2.currentText())

        if not self.serial_thread.is_serial_open:
            connect_serial(port, baudrate)
        else:
            # 使用 threading.Thread 启动一个新线程进行关闭和重连操作
            threading.Thread(target=close_and_reconnect, daemon=True).start()

    def write_config_file(self):
        if not config.has_section('size'):
            config.add_section('size')
        config.set('size', '操作延时', str(self.ksize_3.text()))

        if not config.has_section('threshold'):
            config.add_section('threshold')

        config.set('threshold', 'len_result', str(self.lineEdit_11.text()))
        config.set('threshold', 'max_value', str(self.lineEdit_12.text()))
        config.set('threshold', 'sum_result', str(self.lineEdit_13.text()))
        self.set_yanshi()

        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'), 'w',
                  encoding='utf-8') as configfile:
            config.write(configfile)

    @staticmethod
    def on_widgetDisplay1_clicked(image_path, event):
        # 在点击事件处理函数中显示放大后的图像
        # 这里仅为示例，您需要根据需求自行实现具体的放大操作
        image_path = image_path
        image = QtGui.QImage(image_path)
        enlarged_window = EnlargedWindow(image)
        enlarged_window.exec_()

    def handle_link_clicked(self, url):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        self.update_text_display()

    def update_text_display(self):
        # 假设这里是更新 text_display 的方法，根据需要重新设置内容
        existing_text = self.text_display.toHtml().strip()  # 获取当前文本的方式
        self.text_display.setHtml(existing_text)

    def toggleMode(self):
        if self.mode == 'production':
            login_dialog = LoginDialog(self.widget)
            if login_dialog.exec_() == QDialog.Accepted:
                self.mode = 'admin'
                self.verticalLayout_3.setEnabled(True)
                self.set_layout_widgets_enabled(self.verticalLayout_3, True)
                self.buttonx.setText("管理员模式")
                self.pushButton_4.setText("管理员模式")
                self.start_event_detection()
                print("切换到管理员模式")
        else:
            self.mode = 'production'
            self.set_layout_widgets_enabled(self.verticalLayout_3, False)
            self.pushButton_4.setText("生产模式")
            self.buttonx.setText("生产模式")
            self.stop_event_detection()

    def start_event_detection(self):
        self.last_activity_time = time.time()
        if self.keyboard_listener is None:
            self.keyboard_listener = keyboard.Listener(on_press=self.on_keyboard_event)
        if self.mouse_listener is None:
            self.mouse_listener = mouse.Listener(on_move=self.on_mouse_event)
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def stop_event_detection(self):
        if self.keyboard_listener is not None:
            self.keyboard_listener.stop()
            self.keyboard_listener = None  # Reset to None after stopping
        if self.mouse_listener is not None:
            self.mouse_listener.stop()
            self.mouse_listener = None  # Reset to None after stopping

    def on_keyboard_event(self, key):
        self.last_activity_time = time.time()

    def on_mouse_event(self, x, y):
        self.last_activity_time = time.time()

    def check_inactivity(self):
        if self.mode == 'admin':
            current_time = time.time()
            if current_time - self.last_activity_time >= 180:
                self.toggleMode()

    def set_layout_widgets_enabled(self, layout, enabled):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if isinstance(item, QtWidgets.QWidgetItem):
                widget = item.widget()
                widget.setEnabled(enabled)
            elif isinstance(item, QtWidgets.QLayoutItem):
                child_layout = item.layout()
                if child_layout is not None:
                    self.set_layout_widgets_enabled(child_layout, enabled)

    def enable_layout_widgets(self, layout):  # 解禁
        self.tab_3.setEnabled(True)
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if isinstance(item, QtWidgets.QWidgetItem):
                widget = item.widget()
                widget.setEnabled(True)
            elif isinstance(item, QtWidgets.QLayoutItem):
                child_layout = item.layout()
                if child_layout is not None:
                    self.enable_layout_widgets(child_layout)

    def duqu_yanshi(self):
        return self.yanshi.value()

    @staticmethod
    def save_yanshi(yanshiold):

        if not config.has_section('yanshi'):
            config.add_section('yanshi')
        config.set('yanshi', 'yanshi1', str(yanshiold))
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'), 'w',
                  encoding='utf-8') as configfile:
            config.write(configfile)

    def set_yanshi(self):
        yanshi = self.duqu_yanshi()
        self.save_yanshi(yanshi)
        self.text_display.append(f"您设置的取图延时是{yanshi}秒")

    @staticmethod
    def duqu_yanshi_config():
        try:
            if not config.has_section('yanshi'):
                config.add_section('yanshi')
            threshold = config.get('yanshi', 'yanshi1')
        except FileNotFoundError:
            threshold = 0.5
        return float(threshold)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    mainWindow = QMainWindow()

    window = Ui_MainWindow()
    window.setupUi(mainWindow)

    mainWindow.show()
    sys.exit(app.exec_())
