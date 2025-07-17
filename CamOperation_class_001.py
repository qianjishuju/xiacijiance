# -- coding: utf-8 --
import datetime
import threading
import time
import ctypes
import cv2
import numpy as np
import sys
import inspect
import random
from PyQt5.QtCore import pyqtSignal

sys.path.append("MvImport")
from MvImport.MvCameraControl_class import *


# 强制关闭线程
def Async_raise(tid, exctype):
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


# 停止线程
def Stop_thread(thread):
    Async_raise(thread.ident, SystemExit)


# 转为16进制字符串
def To_hex_str(num):
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


# 相机操作类
class CameraOperation:
    image_processed = pyqtSignal(np.ndarray)

    def __init__(self, obj_cam, st_device_list, n_connect_num=0, b_open_device=False, b_start_grabbing=False,
                 h_thread_handle=None,
                 b_thread_closed=False, st_frame_info=None, b_exit=False, b_save_bmp=False, b_save_jpg=False,
                 buf_save_image=None,
                 n_save_image_size=0, n_win_gui_id=0, frame_rate=0, exposure_time=0, gain=0):

        self.last_frame_time = time.time()
        self.frame_count = 0

        self.obj_cam = obj_cam
        self.st_device_list = st_device_list
        self.n_connect_num = n_connect_num
        self.b_open_device = b_open_device
        self.b_start_grabbing = b_start_grabbing
        self.b_thread_closed = b_thread_closed
        self.st_frame_info = st_frame_info
        self.b_exit = b_exit
        self.b_save_bmp = b_save_bmp
        self.b_save_jpg = b_save_jpg
        self.buf_grab_image = None
        self.buf_grab_image_size = 0
        self.buf_save_image = buf_save_image
        self.n_save_image_size = n_save_image_size
        self.h_thread_handle = h_thread_handle
        self.frame_rate = frame_rate
        self.exposure_time = exposure_time
        self.gain = gain
        self.buf_lock = threading.Lock()  # 取图和存图的buffer锁

    # 打开相机
    def Open_device(self):
        if not self.b_open_device:
            if self.n_connect_num < 0:
                return MV_E_CALLORDER

            # ch:选择设备并创建句柄 | en:Select device and create handle
            nConnectionNum = int(self.n_connect_num)
            stDeviceList = cast(self.st_device_list.pDeviceInfo[int(nConnectionNum)],
                                POINTER(MV_CC_DEVICE_INFO)).contents
            self.obj_cam = MvCamera()
            ret = self.obj_cam.MV_CC_CreateHandle(stDeviceList)
            if ret != 0:
                self.obj_cam.MV_CC_DestroyHandle()
                return ret

            ret = self.obj_cam.MV_CC_OpenDevice()
            if ret != 0:
                return ret
            print("open device successfully!")
            self.b_open_device = True
            self.b_thread_closed = False

            # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
            if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
                nPacketSize = self.obj_cam.MV_CC_GetOptimalPacketSize()
                if int(nPacketSize) > 0:
                    ret = self.obj_cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                    if ret != 0:
                        print("warning: set packet size fail! ret[0x%x]" % ret)
                else:
                    print("warning: set packet size fail! ret[0x%x]" % nPacketSize)

            stBool = c_bool(False)
            ret = self.obj_cam.MV_CC_GetBoolValue("AcquisitionFrameRateEnable", stBool)
            if ret != 0:
                print("get acquisition frame rate enable fail! ret[0x%x]" % ret)

            # ch:设置触发模式为off | en:Set trigger mode as off
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
            if ret != 0:
                print("set trigger mode fail! ret[0x%x]" % ret)
            return MV_OK


    def Start_grabbing(self):
        if not self.b_start_grabbing and self.b_open_device:
            self.b_exit = False
            ret = self.obj_cam.MV_CC_StartGrabbing()
            if ret != 0:
                return ret
            self.b_start_grabbing = True
            print("start grabbing successfully!")
            try:
                self.h_thread_handle = threading.Thread(target=CameraOperation.Work_thread, args=(self, ))
                self.h_thread_handle.start()
                self.b_thread_closed = True
            finally:
                pass
            return MV_OK

        return MV_E_CALLORDER

    # 停止取图
    def Stop_grabbing(self):
        if self.b_start_grabbing and self.b_open_device:
            # 退出线程
            if self.b_thread_closed:
                Stop_thread(self.h_thread_handle)
                self.b_thread_closed = False
            ret = self.obj_cam.MV_CC_StopGrabbing()
            if ret != 0:
                return ret
            print("stop grabbing successfully!")
            self.b_start_grabbing = False
            self.b_exit = True
            return MV_OK
        else:
            return MV_E_CALLORDER

    # 关闭相机
    def Close_device(self):
        if self.b_open_device:
            # 退出线程
            if self.b_thread_closed:
                Stop_thread(self.h_thread_handle)
                self.b_thread_closed = False
            ret = self.obj_cam.MV_CC_CloseDevice()
            if ret != 0:
                return ret

        # ch:销毁句柄 | Destroy handle
        self.obj_cam.MV_CC_DestroyHandle()
        self.b_open_device = False
        self.b_start_grabbing = False
        self.b_exit = True
        print("close device successfully!")

        return MV_OK

    # 设置触发模式
    def Set_trigger_mode(self, is_trigger_mode):
        if not self.b_open_device:
            return MV_E_CALLORDER

        if not is_trigger_mode:
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", 0)
            if ret != 0:
                return ret
        else:
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", 1)
            if ret != 0:
                return ret
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerSource", 7)
            if ret != 0:
                return ret

        return MV_OK

    # 软触发一次
    def Trigger_once(self):
        if self.b_open_device:
            return self.obj_cam.MV_CC_SetCommandValue("TriggerSoftware")

    # 获取参数
    def Get_parameter(self):
        if self.b_open_device:
            stFloatParam_FrameRate = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_FrameRate), 0, sizeof(MVCC_FLOATVALUE))
            stFloatParam_exposureTime = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_exposureTime), 0, sizeof(MVCC_FLOATVALUE))
            stFloatParam_gain = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_gain), 0, sizeof(MVCC_FLOATVALUE))
            ret = self.obj_cam.MV_CC_GetFloatValue("AcquisitionFrameRate", stFloatParam_FrameRate)
            if ret != 0:
                return ret
            self.frame_rate = stFloatParam_FrameRate.fCurValue

            ret = self.obj_cam.MV_CC_GetFloatValue("ExposureTime", stFloatParam_exposureTime)
            if ret != 0:
                return ret
            self.exposure_time = stFloatParam_exposureTime.fCurValue

            ret = self.obj_cam.MV_CC_GetFloatValue("Gain", stFloatParam_gain)
            if ret != 0:
                return ret
            self.gain = stFloatParam_gain.fCurValue

            return MV_OK

    # 设置参数
    def Set_parameter(self, frameRate, exposureTime, gain):
        if '' == frameRate or '' == exposureTime or '' == gain:
            print('show info', 'please type in the text box !')
            return MV_E_PARAMETER
        if self.b_open_device:
            ret = self.obj_cam.MV_CC_SetFloatValue("ExposureTime", float(exposureTime))
            if ret != 0:
                print('show error', 'set exposure time fail! ret = ' + To_hex_str(ret))
                return ret

            ret = self.obj_cam.MV_CC_SetFloatValue("Gain", float(gain))
            if ret != 0:
                print('show error', 'set gain fail! ret = ' + To_hex_str(ret))
                return ret

            ret = self.obj_cam.MV_CC_SetFloatValue("AcquisitionFrameRate", float(frameRate))
            if ret != 0:
                print('show error', 'set acquistion frame rate fail! ret = ' + To_hex_str(ret))
                return ret

            print('show info', 'set parameter success!')

            return MV_OK

    # 取图线程函数
    def Work_thread(self):
        st_out_frame = MV_FRAME_OUT()
        memset(byref(st_out_frame), 0, sizeof(st_out_frame))

        while not self.b_exit:  # 使用 b_exit 作为退出条件
            try:
                ret = self.obj_cam.MV_CC_GetImageBuffer(st_out_frame, 1000)
                if ret == 0:
                    print(f"Successfully grabbed a frame with FrameNum: {st_out_frame.stFrameInfo.nFrameNum}")
                    # 确保缓存被正确初始化
                    if self.buf_save_image is None:
                        print("Initializing buf_save_image")
                        self.buf_save_image = (c_ubyte * st_out_frame.stFrameInfo.nFrameLen)()
                    self.st_frame_info = st_out_frame.stFrameInfo
                    # 锁定缓存区并拷贝数据
                    with self.buf_lock:
                        cdll.msvcrt.memcpy(byref(self.buf_save_image), st_out_frame.pBufAddr,
                                           self.st_frame_info.nFrameLen)
                    self.obj_cam.MV_CC_FreeImageBuffer(st_out_frame)
                else:
                    print(f"Failed to grab a frame, error code: {To_hex_str(ret)}")

                    continue  # 继续尝试获取图像


            except Exception as e:
                print(f"Error in work_thread: {e}")
                # 在异常情况下退出循环

        if self.buf_save_image is not None:
            del self.buf_save_image

    # 存jpg图像
    def Save_jpg(self):

        if self.buf_save_image is None:
            return

        # 获取缓存锁
        self.buf_lock.acquire()

        file_path = str(self.st_frame_info.nFrameNum) + ".jpg"

        stSaveParam = MV_SAVE_IMG_TO_FILE_PARAM()
        stSaveParam.enPixelType = self.st_frame_info.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
        stSaveParam.nWidth = self.st_frame_info.nWidth  # ch:相机对应的宽 | en:Width
        stSaveParam.nHeight = self.st_frame_info.nHeight  # ch:相机对应的高 | en:Height
        stSaveParam.nDataLen = self.st_frame_info.nFrameLen
        stSaveParam.pData = cast(self.buf_save_image, POINTER(c_ubyte))
        stSaveParam.enImageType = MV_Image_Jpeg  # ch:需要保存的图像类型 | en:Image format to save
        stSaveParam.nQuality = 80
        stSaveParam.pImagePath = file_path.encode('ascii')
        stSaveParam.iMethodValue = 2
        ret = self.obj_cam.MV_CC_SaveImageToFile(stSaveParam)

        self.buf_lock.release()
        return ret

    # 存BMP图像
    def Save_Bmp(self):

        if 0 == self.buf_save_image:
            return

        # 获取缓存锁
        self.buf_lock.acquire()

        file_path = str(self.st_frame_info.nFrameNum) + ".bmp"

        stSaveParam = MV_SAVE_IMG_TO_FILE_PARAM()
        stSaveParam.enPixelType = self.st_frame_info.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
        stSaveParam.nWidth = self.st_frame_info.nWidth  # ch:相机对应的宽 | en:Width
        stSaveParam.nHeight = self.st_frame_info.nHeight  # ch:相机对应的高 | en:Height
        stSaveParam.nDataLen = self.st_frame_info.nFrameLen
        stSaveParam.pData = cast(self.buf_save_image, POINTER(c_ubyte))
        stSaveParam.enImageType = MV_Image_Bmp  # ch:需要保存的图像类型 | en:Image format to save
        stSaveParam.nQuality = 8
        stSaveParam.pImagePath = file_path.encode('ascii')
        stSaveParam.iMethodValue = 2
        ret = self.obj_cam.MV_CC_SaveImageToFile(stSaveParam)

        self.buf_lock.release()

        return ret

    def capture_frame(self):
        if self.buf_save_image is None:
            print("Buffer is empty, no image captured.")
            return None

        # 获取缓存锁
        self.buf_lock.acquire()

        try:
            print("Buffer is not empty, attempting to decode image.")
            # 将缓冲区中的图像数据转换为字节数组
            jpg_data = string_at(self.buf_save_image, self.st_frame_info.nFrameLen)

            # 将JPEG数据转换为NumPy数组（相当于cv2.imread读取的图像数据）
            image_np = cv2.imdecode(np.frombuffer(jpg_data, np.uint8), cv2.IMREAD_COLOR)

            if image_np is None:
                print("Failed to decode image from buffer.")

        finally:
            # 释放缓存锁
            self.buf_lock.release()

        return image_np

    # def capture_frame(self):
    #     try:
    #
    #         print("截取图像帧", datetime.datetime.now())
    #         print("获取图像帧前的锁状态:", self.buf_lock.locked())
    #         print("缓存状态:", self.buf_save_image)
    #
    #         self.buf_lock.acquire()
    #
    #         if self.buf_save_image is None:
    #             print("错误: buf_save_image 为 None", datetime.datetime.now())
    #             self.buf_lock.release()
    #             return None
    #
    #         # captured_frame = self.buf_save_image[:]
    #         print("captured_frame", datetime.datetime.now())
    #         captured_frame_array = np.frombuffer(self.buf_save_image, dtype=np.uint8)
    #
    #         # captured_frame_array = np.frombuffer(captured_frame, dtype=np.uint8)
    #         # captured_frame_array = np.array(captured_frame, dtype=np.uint8)
    #         print("captured_frame_array", datetime.datetime.now())
    #
    #         # # 添加调试输出
    #         # print("原始图像维度:", captured_frame_array.shape)
    #         # print("图像信息:", self.st_frame_info)
    #         # 获取图像信息
    #         enGvspPixelType = self.st_frame_info.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
    #         print(enGvspPixelType)
    #
    #         # 检查图像类型
    #         if Is_mono_data(enGvspPixelType):
    #             captured_frame_rgb = cv2.cvtColor(captured_frame_array,
    #                                               cv2.COLOR_GRAY2RGB)  # 如果captured_frame_array是灰度就启用，如果不是就不用。
    #             numArray = captured_frame_rgb.reshape((self.st_frame_info.nHeight, self.st_frame_info.nWidth, 3))
    #             self.buf_lock.release()
    #             print("Is_mono_datadatetime", datetime.datetime.now())
    #             return numArray
    #         elif Is_color_data(enGvspPixelType):
    #             captured_frame_rgb = cv2.cvtColor(captured_frame_array,
    #                                               cv2.COLOR_GRAY2RGB)  # 如果captured_frame_array是灰度就启用，如果不是就不用。
    #             numArray = captured_frame_rgb.reshape((self.st_frame_info.nHeight, self.st_frame_info.nWidth, 3))
    #             self.buf_lock.release()
    #             print("Is_color_data", datetime.datetime.now())
    #             return numArray
    #         elif Is_RGB_data(enGvspPixelType):
    #             numArray = captured_frame_array.reshape(
    #                 (self.st_frame_info.nHeight, self.st_frame_info.nWidth, 3))
    #             self.buf_lock.release()
    #
    #             print("Is_RGB_data", datetime.datetime.now())
    #             return numArray
    #         else:
    #             print("不支持的图像类型")
    #             self.buf_lock.release()
    #             return None
    #     except Exception as e:
    #         print("capture_frame中发生错误:", e)
    #         return None
