# -- coding: utf-8 --
import asyncio
import logging

import os
import threading

import cv2
import time

import numpy as np
from PIL import Image
from datetime import datetime
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt, QThread, QMetaObject, pyqtSlot, Q_ARG, QEventLoop, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import *
from CamOperation_class import CameraOperation
from MvImport.MvCameraControl_class import *
from MvImport.MvErrorDefine_const import *
from MvImport.CameraParams_header import *
from PyUICBasicDemo_4_ui import Ui_MainWindow, config

from 异物识别训练代码.yiwu_model_warp import wrapper_yiwu
from 圆识别训练代码.yuan_model_warp import wrapper_yuan
from 贴胶识别训练代码.teijiao_warp import wrapper_tiejiao

# 重定向 print 输出到文件,log

import torch




# 设置日志记录器
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# 创建一个文件处理器
log_handler = logging.FileHandler('debug_output.txt', encoding="utf-8")
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# 将处理器添加到日志记录器
logger.addHandler(log_handler)

# 创建线程锁
loop = asyncio.get_event_loop()
print("Current working directory:", os.getcwd())

print("CUDA available:", torch.cuda.is_available())
logger.debug(f"CUDA available: {torch.cuda.is_available()}")


try:
    yuan1 = wrapper_yuan(config.get("folder_path", "yuan_model"), cuda=torch.cuda.is_available())
    yiwu1 = wrapper_yiwu(config.get("folder_path", "yiwu_model"), cuda=torch.cuda.is_available())
    tiejiao1 = wrapper_tiejiao(config.get("folder_path", "tiejiao_model"), cuda=torch.cuda.is_available())

except Exception as e:
    logger.debug(f"请选择模型位置，具体错误信息: {e}, 错误类型: {type(e).__name__}")


def TxtWrapBy(start_str, end, all):
    start = all.find(start_str)
    if start >= 0:
        start += len(start_str)
        end = all.find(end, start)
        if end >= 0:
            return all[start:end].strip()


# 将返回的错误码转换为十六进制显示
def ToHexStr(num):
    chaDic = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
    hexStr = ""
    if num < 0:
        num = num + 2 ** 32
    while num >= 16:
        digit = num % 16
        hexStr = chaDic.get(digit, str(digit)) + hexStr
        num //= 16
    hexStr = chaDic.get(num, str(num)) + hexStr
    return hexStr


if __name__ == "__main__":
    global deviceList
    deviceList = MV_CC_DEVICE_INFO_LIST()
    global cam
    cam = MvCamera()
    global nSelCamIndex
    nSelCamIndex = 0
    global obj_cam_operation
    obj_cam_operation = 0
    global isOpen
    isOpen = False
    global isGrabbing
    isGrabbing = False
    global isCalibMode  # 是否是标定模式（获取原始图像）
    isCalibMode = True
    global show_links  # 控制链接文本的显示状态
    show_links = True

    curr_time = datetime.now()
    time_str = datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S.%f')
    print("开始时间：", time_str)


    # 绑定下拉列表至设备信息索引
    def xFunc(event):
        global nSelCamIndex
        nSelCamIndex = TxtWrapBy("[", "]", ui.ComboDevices.get())


    # ch:枚举相机 | en:enum devices
    def enum_devices():
        global deviceList
        global obj_cam_operation

        deviceList = MV_CC_DEVICE_INFO_LIST()
        ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, deviceList)
        if ret != 0:
            strError = "Enum devices fail! ret = :" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.Ok)
            return ret

        if deviceList.nDeviceNum == 0:
            QMessageBox.warning(mainWindow, "Info", "Find no device", QMessageBox.Ok)
            return ret
        print("Find %d devices!" % deviceList.nDeviceNum)

        devList = []
        for i in range(0, deviceList.nDeviceNum):
            mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                print("\ngige device: [%d]" % i)
                chUserDefinedName = ""
                for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chUserDefinedName:
                    if 0 == per:
                        break
                    chUserDefinedName = chUserDefinedName + chr(per)
                print("device user define name: %s" % chUserDefinedName)

                chModelName = ""
                for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                    if 0 == per:
                        break
                    chModelName = chModelName + chr(per)

                print("device model name: %s" % chModelName)

                nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
                devList.append(
                    "[" + str(i) + "]GigE: " + chUserDefinedName + " " + chModelName + "(" + str(nip1) + "." + str(
                        nip2) + "." + str(nip3) + "." + str(nip4) + ")")
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print("\nu3v device: [%d]" % i)
                chUserDefinedName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chUserDefinedName:
                    if per == 0:
                        break
                    chUserDefinedName = chUserDefinedName + chr(per)
                print("device user define name: %s" % chUserDefinedName)

                chModelName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                    if 0 == per:
                        break
                    chModelName = chModelName + chr(per)
                print("device model name: %s" % chModelName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)
                devList.append("[" + str(i) + "]USB: " + chUserDefinedName + " " + chModelName
                               + "(" + str(strSerialNumber) + ")")

        ui.ComboDevices.clear()
        ui.ComboDevices.addItems(devList)
        ui.ComboDevices.setCurrentIndex(0)


    # ch:打开相机 | en:open device
    def open_device():
        global deviceList
        global nSelCamIndex
        global obj_cam_operation
        global isOpen
        if isOpen:
            QMessageBox.warning(mainWindow, "Error", 'Camera is Running!', QMessageBox.Ok)
            return MV_E_CALLORDER

        nSelCamIndex = ui.ComboDevices.currentIndex()
        if nSelCamIndex < 0:
            QMessageBox.warning(mainWindow, "Error", 'Please select a camera!', QMessageBox.Ok)
            return MV_E_CALLORDER

        obj_cam_operation = CameraOperation(cam, deviceList, nSelCamIndex)

        ret = obj_cam_operation.Open_device()
        if 0 != ret:
            strError = "Open device failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.Ok)
            isOpen = False
        else:
            set_continue_mode()

            get_param()

            isOpen = True
            enable_controls()


    # ch:开始取流 | en:Start grab image
    def start_grabbing():
        global obj_cam_operation
        global isGrabbing
        try:
            ret = obj_cam_operation.Start_grabbing()
            if ret != 0:
                strError = "Start grabbing failed ret:" + ToHexStr(ret)
                QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.Ok)
            else:
                isGrabbing = True
                enable_controls()
        except Exception as e:
            logger.debug(f'取流失败{e}')




    # ch:停止取流 | en:Stop grab image
    def stop_grabbing():
        global obj_cam_operation
        global isGrabbing
        ret = obj_cam_operation.Stop_grabbing()
        if ret != 0:
            strError = "Stop grabbing failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.Ok)
        else:
            isGrabbing = False
            enable_controls()


    # ch:关闭设备 | Close device
    def close_device():
        global isOpen
        global isGrabbing
        global obj_cam_operation

        if isOpen:
            obj_cam_operation.Close_device()
            isOpen = False

        isGrabbing = False

        enable_controls()


    # ch:设置触发模式 | en:set trigger mode
    def set_continue_mode():
        strError = None

        ret = obj_cam_operation.Set_trigger_mode(True)
        if ret != 0:
            strError = "Set continue mode failed ret:" + ToHexStr(ret) + " mode is " + str("is_trigger_mode")
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.Ok)
        else:
            ui.radioContinueMode.setChecked(False)
            ui.radioTriggerMode.setChecked(True)
            ui.bnSoftwareTrigger.setEnabled(True)


    # ch:设置软触发模式 | en:set software trigger mode
    def set_software_trigger_mode():

        ret = obj_cam_operation.Set_trigger_mode(True)
        if ret != 0:
            strError = "Set trigger mode failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.Ok)
        else:
            ui.radioContinueMode.setChecked(True)
            ui.radioTriggerMode.setChecked(False)
            ui.bnSoftwareTrigger.setEnabled(isGrabbing)


    # ch:设置触发命令 | en:set trigger software
    def trigger_once():
        ret = obj_cam_operation.Trigger_once()
        print("ret:", ret)
        if ret != 0:
            print(ret, "TriggerSoftware failed")
            strError = "TriggerSoftware failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.Ok)


    # ch:存图 | en:save image
    def save_bmp():
        ret = obj_cam_operation.Save_Bmp()
        print("图片保存", ret)
        if ret != MV_OK:
            strError = "Save BMP failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.Ok)
        else:
            print("Save image success")


    # ch: 获取参数 | en:get param
    def get_param():
        ret = obj_cam_operation.Get_parameter()
        if ret != MV_OK:
            strError = "Get param failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.Ok)
        else:
            ui.edtExposureTime.setText("{0:.2f}".format(obj_cam_operation.exposure_time))
            ui.edtGain.setText("{0:.2f}".format(obj_cam_operation.gain))
            ui.edtFrameRate.setText("{0:.2f}".format(obj_cam_operation.frame_rate))


    # ch: 设置参数 | en:set param
    def set_param():
        frame_rate = ui.edtFrameRate.text()
        exposure = ui.edtExposureTime.text()
        gain = ui.edtGain.text()
        ret = obj_cam_operation.Set_parameter(frame_rate, exposure, gain)
        if ret != MV_OK:
            strError = "Set param failed ret:" + ToHexStr(ret)
            QMessageBox.warning(mainWindow, "Error", strError, QMessageBox.Ok)

        return MV_OK


    # ch: 设置控件状态 | en:set enable status
    def enable_controls():
        global isGrabbing
        global isOpen

        # 先设置group的状态，再单独设置各控件状态
        ui.groupGrab.setEnabled(isOpen)
        ui.groupParam.setEnabled(isOpen)

        ui.bnOpen.setEnabled(not isOpen)
        ui.bnClose.setEnabled(isOpen)

        ui.bnStart.setEnabled(isOpen and (not isGrabbing))
        ui.bnStop.setEnabled(isOpen and isGrabbing)
        ui.bnSoftwareTrigger.setEnabled(isGrabbing and ui.radioTriggerMode.isChecked())

        ui.bnSaveImage.setEnabled(isOpen and isGrabbing)


    import numpy as np
    from PyQt5.QtGui import QImage


    def array_to_qimage(array):
        if array.dtype != np.uint8:
            raise ValueError("必须是 np.uint8 类型")
        if len(array.shape) != 3 or array.shape[2] != 3:
            raise ValueError("必须是形状为 (H, W, 3) 的 RGB 图像")
        if not array.flags['C_CONTIGUOUS']:
            array = np.ascontiguousarray(array)

        height, width, _ = array.shape
        bytes_per_line = width * 3
        return QImage(array.data, width, height, bytes_per_line, QImage.Format_RGB888)

    async def on_capture(content, ui):
        try:
            if not os.path.exists(ui.windows_path):
                os.makedirs(ui.windows_path, exist_ok=True)
                ui.text_display.append("请选择图片保存路径")
                logger.error("请选择图片保存路径")
            print(f"接收到的数据: {content}")
            if content.strip():
                content = content.strip()
                trigger_once()
                await asyncio.sleep(ui.duqu_yanshi())
                print(content)
                if 25 > len(content) > 10:
                    await caiji_process_frame(ui, content)
                else:
                    ui.text_display.append(f"条码长度有错误，实际长度{len(content)}")
                    logger.error(f"条码长度有错误，实际长度{len(content)}")
            else:
                ui.text_display.append("接收触发信号异常")
                logger.error("接收触发信号异常")
        except Exception as e:
            print(f"发生错误: {e}")


    def pil_image_to_qimage(pil_image: Image) -> QImage:
        pil_image = pil_image.convert("RGB")
        width, height = pil_image.size
        qimage = QImage(pil_image.tobytes(), width, height, pil_image.width * 3, QImage.Format_RGB888)
        return qimage


    def pil_image_to_pixmap(pil_image: Image) -> QPixmap:
        qimage = pil_image_to_qimage(pil_image)
        pixmap = QPixmap.fromImage(qimage)
        return pixmap


    # 在主线程中更新UI
    def update_ui(Display, qimage):
        if qimage is None:
            Display.clear()  # 清除 Display 的显示内容
            return
        pixmap = QtGui.QPixmap.fromImage(qimage)
        scaled_pixmap = pixmap.scaled(Display.size(), Qt.KeepAspectRatio)
        Display.setPixmap(scaled_pixmap)

    import 小窗_ui


    async def show_anomaly_dialog_async(parent_widget, qimage):
        # 创建一个 QDialog
        dialog = 小窗_ui.ResizableDialog(parent_widget, qimage)

        # 用于存储用户的选择和触发方式
        result = {"status": None, "trigger": None}  # 新增 trigger 字段

        def on_yes():
            result["status"] = "YES"
            result["trigger"] = "manual"  # 标记为手动触发
            timer.stop()  # 停止计时器
            dialog.accept()

        def on_no():
            result["status"] = "NO"
            result["trigger"] = "manual"  # 标记为手动触发
            timer.stop()  # 停止计时器
            dialog.reject()

        def on_timeout():
            result["status"] = "NO"
            result["trigger"] = "timeout"  # 标记为超时触发
            dialog.reject()

        # 连接按钮的点击事件
        dialog.ui.pushButton.clicked.connect(on_yes)
        dialog.ui.pushButton_2.clicked.connect(on_no)

        # 设置定时器
        timer = QtCore.QTimer()
        timer.setSingleShot(True)  # 单次触发
        timer.timeout.connect(on_timeout)  # 超时后执行 on_timeout 函数
        timer.start(int(config.get('size', 'caozuoyanshi')))  # 30秒超时

        # 显示对话框（非模态）
        dialog.show()

        # 强制刷新 UI
        QtWidgets.QApplication.processEvents()
        # 显示模态对话框并等待用户操作
        dialog.exec_()

        # 返回用户的选择和触发方式
        return result["status"], result["trigger"]


    async def caiji_process_frame(ui, content):
        status = "FAIL"
        logger.debug("测试开始时间：%s", datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S.%f'))

        try:
            # # 检查相机是否处于抓取状态
            # if not isGrabbing:
            #     print("错误: 相机未处于抓取状态")
            #     logger.debug("错误: 相机未处于抓取状态")
            #     return

            # capture_frame = obj_cam_operation.capture_frame()
            # 获取图像帧


            try:
                file_path = r"C:\Users\Administrator\Desktop\11\CCD\DK3HF300GJY0000SK0CC_PASS_20250421162308_1.jpg"
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"文件 {file_path} 不存在。")

                # 检查文件权限
                if not os.access(file_path, os.R_OK):
                    raise PermissionError(f"没有权限访问文件 {file_path}。")

                # 读取图像
                capture_frame = cv2.imread(file_path)

                if capture_frame is None:
                    raise ValueError("无法读取图像，可能文件已损坏。")

            except FileNotFoundError as e:
                print(e)
            except PermissionError as e:
                print(e)
            except ValueError as e:
                print(e)
            except Exception as e:
                print(f"发生未知错误: {e}")




            capture_frame_rgb = cv2.cvtColor(capture_frame, cv2.COLOR_BGR2RGB)
            capture_frame_pil = Image.fromarray(capture_frame_rgb)
            qimage = array_to_qimage(capture_frame_rgb)

            # 异步更新UI
            await asyncio.gather(
                asyncio.get_event_loop().run_in_executor(None, lambda: update_ui(ui.widgetDisplay, qimage)),
                asyncio.get_event_loop().run_in_executor(None, lambda: update_ui(ui.label_13, None)),
                asyncio.get_event_loop().run_in_executor(None, lambda: update_ui(ui.label_14, None))
            )

            if capture_frame.size > 0:
                tiejiao_image, class_areas, value = tiejiao1.detect_image(capture_frame_pil)
                result_pixmap = pil_image_to_qimage(tiejiao_image)
                await asyncio.get_event_loop().run_in_executor(None, lambda: update_ui(ui.label_13, result_pixmap))

                array = np.array(class_areas)
                result = array[1:]
                sum_result = np.sum(result)
                max_value = np.max(result)
                value = value[1]

                if value[0] is None or value[1] is None:
                    ui.text_display.append("贴胶识别失败，没有检测到贴胶区域")
                    logger.debug("贴胶识别失败，没有检测到贴胶区域")
                    raise ValueError("贴胶识别失败，没有检测到贴胶区域")
                else:
                    ui.text_display.append(f"获取贴胶识别到区域面积总和 {sum_result}")
                    logger.debug(f"获取贴胶识别到区域面积总和 {sum_result}")

                    if sum_result > int(config.get("threshold", "sum_result")):
                        result_image1, class_areas1, center_points1 = yuan1.detect_image(capture_frame_pil)
                        result_pixmap1 = pil_image_to_qimage(result_image1)
                        await asyncio.get_event_loop().run_in_executor(None,
                                                                       lambda: update_ui(ui.label_14, result_pixmap1))

                        array1 = np.array(class_areas1)
                        resultq = array1[1:]
                        sum_result1 = np.sum(resultq)
                        max_value1 = np.max(resultq)
                        result1 = center_points1[1]

                        if result1[0] is None or result1[1] is None:
                            ui.text_display.append("圆识别失败，没有检测到MIC区域")
                            logger.debug("圆识别失败，没有检测到MIC区域")
                            raise ValueError("圆识别失败，没有检测到MIC区域")
                        else:
                            center_x, center_y = result1
                            r = int(config.get('size', 'banjing'))

                            x1, y1 = max(center_x - r, 0), max(center_y - r, 0)
                            x2, y2 = min(center_x + r, capture_frame_pil.width), min(center_y + r,
                                                                                     capture_frame_pil.height)

                            cropped_image = capture_frame_pil.crop((x1, y1, x2, y2))
                            ui.text_display.append(f"区域累计面积 {sum_result1}")
                            logger.debug(f"区域累计面积 {sum_result1}")

                            if 80000 < sum_result1 < 120000:
                                yiwu_image, class_areas2 = yiwu1.detect_image(cropped_image)

                                array2 = np.array(class_areas2)
                                result2 = array2[1:]
                                sum_result2 = np.sum(result2)
                                max_value2 = np.max(result2)
                                len_result2 = len(result2)


                                ui.text_display.append(
                                    f"异物区域累计面积 {sum_result2}, 获取异物识别到区域数量 {len_result2}, 识别到最大区域 {max_value2}")
                                logger.debug(
                                    f"异物区域累计面积 {sum_result2}, 获取异物识别到区域数量 {len_result2}, 识别到最大区域 {max_value2}")
                                # 将裁剪图像中的标记区域映射到原始图像

                                # 将 yiwu_image 转换为 numpy 数组
                                yiwu_array = np.array(yiwu_image)

                                # 创建一个与 capture_frame_pil 相同大小的空白图像
                                capture_frame_array = np.array(capture_frame_pil)
                                # 计算裁剪区域的宽度和高度
                                width = x2 - x1
                                height = y2 - y1

                                # 得出 cropped_box
                                cropped_box = (x1, y1, width, height)
                                # 获取 cropped_image 在 capture_frame_pil 中的位置和大小
                                x, y, w, h = cropped_box

                                # 将识别到的区域映射回 capture_frame_pil
                                capture_frame_array[y:y + h, x:x + w] = yiwu_array

                                # 将更新后的 capture_frame_pil 转换为 QImage
                                qimage = pil_image_to_qimage(Image.fromarray(capture_frame_array))


                                await asyncio.gather(
                                    asyncio.get_event_loop().run_in_executor(None, lambda: update_ui(ui.widgetDisplay,
                                                                                                     qimage)),
                                )



                                if max_value2 < int(config.get("threshold", "max_value")) and len_result2 < int(
                                        config.get("threshold", "len_result")) and sum_result2 < int(
                                    config.get("threshold", "sum_result")):
                                    status = "PASS"
                                    ui.text_display.append("异物检测正常")
                                    logger.debug("异物检测正常")

                                else:
                                    status = "FAIL"
                                    ui.text_display.append("异物检测到異常")
                                    logger.debug("异物检测異常")




                            else:
                                ui.text_display.append("识别到的圆面积异常")
                                logger.debug("识别到的圆面积异常")
                    else:
                        ui.text_display.append(f"请检测贴胶,贴胶面积小于{config.get('threshold', 'sum_result')}")
                        logger.debug(f"请检测贴胶,贴胶面积小于{config.get('threshold', 'sum_result')}")
            else:
                ui.text_display.append("图片为空")
                logger.debug("错误信息: 图片为空")
                print("图片为空")
        except ValueError as e:
            ui.text_display.append(f"ValueError视频线程处理: {e}")
            logger.debug(f"ValueError视频线程处理: {e}")
        except Exception as e:
            ui.text_display.append(f"Exception视频线程处理: {e}")
            logger.debug(f"Exception视频线程处理: {e}")
        finally:
            try:
                if status == "PASS":
                    ui.serial_thread.ser.write(b"OK\r\n")
                    logger.debug("发送给上位机 OK")
                else:
                    ui.serial_thread.ser.write(b"NG\r\n")
                    logger.debug("发送给上位机 NG")

                file_1 = content.strip()
                file_split = file_1.split("_")
                filename = os.path.join(ui.windows_path,
                                        f"{file_split[0]}_{status}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_split[1]}.jpg")
                cv2.imwrite(filename, capture_frame)

                existing_text = ui.text_display.toHtml().strip()
                url = QtCore.QUrl.fromLocalFile(filename)
                url_string = QtCore.QUrl.toEncoded(url).data().decode()
                new_text = f'<a href="{url_string}">图片保存在: {filename}</a>'
                combined_text = f"{existing_text}{new_text}"
                ui.text_display.setHtml(combined_text)

                v_scrollbar = ui.text_display.verticalScrollBar()
                v_scrollbar.setValue(v_scrollbar.maximum())

                logger.debug("执行结束时间: %s", datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S.%f'))
            except Exception as e:
                logger.debug(e)


    def cleanup():
        global ui
        if ui.serial_thread is not None:
            ui.serial_thread.stop()  # 停止串口线程
        QtCore.QCoreApplication.quit()  # 退出应用程序


    # ch: 初始化app, 绑定控件与函数 | en: Init app, bind ui-1 and api
    app = QApplication(sys.argv)
    mainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.serial_thread.start()
    ui.serial_thread.capture_signal.connect(lambda content: loop.run_until_complete(on_capture(content, ui)))

    ui.setupUi(mainWindow)
    ui.bnEnum.clicked.connect(enum_devices)

    try:
        QtCore.QTimer.singleShot(200, enum_devices)  # 延迟1秒查找设备
        # 通过定时器延迟执行设备连接和开始采集
        QtCore.QTimer.singleShot(1000, open_device)  # 延迟1秒连接设备

        QtCore.QTimer.singleShot(2000, start_grabbing)  # 再延迟1秒开始采集

    except:
        pass
    ui.bnOpen.clicked.connect(open_device)
    ui.bnClose.clicked.connect(close_device)
    ui.bnStart.clicked.connect(start_grabbing)
    ui.bnStop.clicked.connect(stop_grabbing)
    ui.text_display.anchorClicked.connect(ui.handle_link_clicked)
    ui.bnSoftwareTrigger.clicked.connect(trigger_once)
    ui.radioTriggerMode.clicked.connect(set_software_trigger_mode)
    ui.radioContinueMode.clicked.connect(set_continue_mode)
    ui.bnGetParam.clicked.connect(get_param)
    ui.bnSetParam.clicked.connect(set_param)
    ui.bnSaveImage.clicked.connect(save_bmp)

    try:
        mainWindow.show()

        timer = QtCore.QTimer()
        timer.timeout.connect(ui.check_inactivity)
        timer.start(1000)  # 每秒检查一次
        app.exec_()
    finally:
        app.aboutToQuit.connect(cleanup)  # 在程序退出前执行cleanup函数
        close_device()
        sys.exit()


