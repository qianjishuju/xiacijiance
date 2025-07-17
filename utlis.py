import threading
import serial
from PyQt5.QtCore import QThread, pyqtSignal, QTimer


class SerialThread(QThread):
    serial_data_received = pyqtSignal(str)
    capture_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.timer = None
        self.content = None
        self.ser = None
        self._run_flag = False
        self.serial_open = False
        self.is_serial_open = False
        self.lock = threading.Lock()

    def run(self):
        try:
            if not self.timer:
                self.timer = QTimer()
                self.timer.timeout.connect(self.process_serial_data)
                self.timer.start(100)

            # 启动事件循环，这样定时器就可以正常工作
            while self._run_flag:
                if self.ser and self.ser.isOpen():
                    with self.lock:
                        data = self.ser.readline().decode("utf-8", errors="ignore").strip()
                        if data:
                            self.content = data
                            print("Emitting capture signal")
                            self.capture_signal.emit(self.content)
        except Exception as e:
            print(f"Error in SerialThreadOne: {e}")
        finally:
            self.stop_serial()

    def process_serial_data(self):
        try:
            if self.ser and self.ser.isOpen():
                with self.lock:
                    data = self.ser.readline().decode("utf-8", errors="ignore").strip()
                    if data:
                        self.content = data
                        print("Emitting capture signal")
                        self.capture_signal.emit(self.content)
            else:
                self.stop_serial()
        except Exception as e:
            print(f"Error processing serial data: {e}")
            self.stop_serial()

    def start_serial(self, port, baudrate):
        try:
            with self.lock:
                self.ser = serial.Serial(port, baudrate, timeout=1)
                self._run_flag = True
                self.serial_open = True
                self.start()
            return True
        except Exception as e:
            print(f"启动串行线程时出错: {e}")
            if self.ser and self.ser.isOpen():
                self.ser.close()
            return False

    def stop_serial(self):
        with self.lock:
            self.stop()
            if self.ser and self.ser.isOpen():
                self.ser.close()
                self.ser = None

    def stop(self):
        self._run_flag = False
        self.serial_open = False
        self.quit()  # 停止事件循环
        self.wait()  # 等待线程退出
