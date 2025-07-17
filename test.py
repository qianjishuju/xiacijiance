import sys
import time
import configparser
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QDialog, QMessageBox
from PyQt5 import QtCore
from pynput import mouse, keyboard

config = configparser.ConfigParser()
config.read('config.ini')

class CustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("调试模式")
        self.resize(300, 200)

        self.mode = 'production'
        self.last_activity_time = time.time()

        self.label = QLabel("当前模式：生产模式")
        self.button = QPushButton("切换到管理员模式")
        self.button.clicked.connect(self.toggleMode)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def toggleMode(self):
        if self.mode == 'production':
            login_dialog = LoginDialog(self)
            if login_dialog.exec_() == QDialog.Accepted:
                self.mode = 'admin'
                self.label.setText("当前模式：管理员模式")
                self.button.setText("切换到生产模式")
                self.start_event_detection()
        else:
            self.mode = 'production'
            self.label.setText("当前模式：生产模式")
            self.button.setText("切换到管理员模式")
            self.stop_event_detection()

    def start_event_detection(self):
        self.last_activity_time = time.time()
        self.keyboard_listener = keyboard.Listener(on_press=self.on_keyboard_event)
        self.mouse_listener = mouse.Listener(on_move=self.on_mouse_event)
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def stop_event_detection(self):
        self.keyboard_listener.stop()
        self.mouse_listener.stop()

    def on_keyboard_event(self, key):
        self.last_activity_time = time.time()

    def on_mouse_event(self, x, y):
        self.last_activity_time = time.time()

    def check_inactivity(self):
        if self.mode == 'admin':
            current_time = time.time()
            if current_time - self.last_activity_time >= 300:
                self.toggleMode()

class LoginDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("登录")
        self.username_label = QLabel("用户名:")
        self.username_input = QLineEdit()
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    custom_widget = CustomWidget()
    custom_widget.show()

    timer = QtCore.QTimer()
    timer.timeout.connect(custom_widget.check_inactivity)
    timer.start(1000)  # 每秒检查一次

    sys.exit(app.exec_())
