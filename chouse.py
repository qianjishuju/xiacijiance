import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QRubberBand
from PyQt5.QtGui import QPixmap, QColor, QCursor, QScreen
from PyQt5.QtCore import Qt, QRect, QPoint, QSize

class ColorPicker(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("抽色工具")
        self.setGeometry(100, 100, 800, 600)

        self.info_label = QLabel("点击按钮以选择颜色区域", self)
        self.info_label.setAlignment(Qt.AlignCenter)

        self.pick_color_button = QPushButton("选择屏幕颜色区域", self)
        self.pick_color_button.clicked.connect(self.start_color_pick)

        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addWidget(self.pick_color_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.origin = QPoint()
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)

    def start_color_pick(self):
        self.hide()
        self.setWindowOpacity(0.5)
        self.showFullScreen()
        QApplication.setOverrideCursor(Qt.CrossCursor)
        self.grabMouse()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()

    def mouseMoveEvent(self, event):
        if self.rubber_band.isVisible():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubber_band.hide()
            self.releaseMouse()
            QApplication.restoreOverrideCursor()
            self.setWindowOpacity(1)
            self.showNormal()
            self.capture_color()

    def capture_color(self):
        rect = self.rubber_band.geometry()
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
        image = screenshot.toImage()

        total_red, total_green, total_blue = 0, 0, 0
        for x in range(image.width()):
            for y in range(image.height()):
                color = QColor(image.pixel(x, y))
                total_red += color.red()
                total_green += color.green()
                total_blue += color.blue()

        num_pixels = image.width() * image.height()
        avg_red = total_red // num_pixels
        avg_green = total_green // num_pixels
        avg_blue = total_blue // num_pixels
        avg_color = QColor(avg_red, avg_green, avg_blue)

        self.info_label.setText(f"RGB: ({avg_red}, {avg_green}, {avg_blue}), HEX: #{avg_red:02x}{avg_green:02x}{avg_blue:02x}".upper())
        self.info_label.setStyleSheet(f"background-color: {avg_color.name()}; color: {'#FFFFFF' if avg_color.lightness() < 128 else '#000000'}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorPicker()
    window.show()
    sys.exit(app.exec_())
