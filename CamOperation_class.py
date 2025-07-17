# -- coding: utf-8 --
import datetime
import logging
import threading
import time

import cv2
import numpy as np
import sys
import inspect
import random
from PyQt5.QtCore import pyqtSignal

sys.path.append("MvImport")
from MvImport.MvCameraControl_class import *


# 设置日志记录器
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# 创建一个文件处理器
log_handler = logging.FileHandler('output.txt', encoding="utf-8")
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# 将处理器添加到日志记录器
logger.addHandler(log_handler)

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


# 是否是Mono图像
def Is_mono_data(enGvspPixelType):
    mono_types = [
        PixelType_Gvsp_Mono8, PixelType_Gvsp_Mono10,
        PixelType_Gvsp_Mono10_Packed, PixelType_Gvsp_Mono12,
        PixelType_Gvsp_Mono12_Packed
    ]

    return enGvspPixelType in mono_types


# 是否是彩色图像
def Is_color_data(enGvspPixelType):
    bayer_types = [

        PixelType_Gvsp_BayerGR8, PixelType_Gvsp_BayerRG8,
        PixelType_Gvsp_BayerGB8, PixelType_Gvsp_BayerBG8,
        PixelType_Gvsp_BayerGR10, PixelType_Gvsp_BayerRG10,
        PixelType_Gvsp_BayerGB10, PixelType_Gvsp_BayerBG10,
        PixelType_Gvsp_BayerGR12, PixelType_Gvsp_BayerRG12,
        PixelType_Gvsp_BayerGB12, PixelType_Gvsp_BayerBG12,
        PixelType_Gvsp_BayerGR10_Packed, PixelType_Gvsp_BayerRG10_Packed,
        PixelType_Gvsp_BayerGB10_Packed, PixelType_Gvsp_BayerBG10_Packed,
        PixelType_Gvsp_BayerGR12_Packed, PixelType_Gvsp_BayerRG12_Packed,
        PixelType_Gvsp_BayerGB12_Packed, PixelType_Gvsp_BayerBG12_Packed,
        PixelType_Gvsp_YUV422_Packed, PixelType_Gvsp_YUV422_YUYV_Packed
    ]

    return enGvspPixelType in bayer_types


def Is_RGB_data(enGvspPixelType):
    rgb_types = [
        PixelType_Gvsp_RGB10_Packed, PixelType_Gvsp_RGB10V1_Packed,
        PixelType_Gvsp_RGB8_Planar, PixelType_Gvsp_RGBA8_Packed,
        PixelType_Gvsp_RGB8_Packed, PixelType_Gvsp_RGB16_Packed,
        PixelType_Gvsp_RGB12_Planar, PixelType_Gvsp_RGB16_Planar,
        PixelType_Gvsp_RGB10V2_Packed, PixelType_Gvsp_RGB12V1_Packed,
        PixelType_Gvsp_RGB10V2_Packed, PixelType_Gvsp_RGB12V1_Packed,
        PixelType_Gvsp_RGB565_Packed
    ]

    return enGvspPixelType in rgb_types


def IS_qita_data(enGvspPixelType):
    types = [PixelType_Gvsp_Coord3D_ABC32,
             PixelType_Gvsp_Coord3D_AB32f,
             PixelType_Gvsp_COORD3D_DEPTH_PLUS_MASK,
             PixelType_Gvsp_YUV411_Packed,
             PixelType_Gvsp_BayerBG12,
             PixelType_Gvsp_Coord3D_AC32f_Planar,
             PixelType_Gvsp_BayerBG10_Packed,
             PixelType_Gvsp_YCBCR709_422_8_CBYCRY,
             PixelType_Gvsp_Coord3D_A32f,
             PixelType_Gvsp_BayerBG12_Packed,
             PixelType_Gvsp_BayerRG12,
             PixelType_Gvsp_BayerRG10,
             PixelType_Gvsp_BayerRG16,
             PixelType_Gvsp_YCBCR709_411_8_CBYYCRYY,
             PixelType_Gvsp_BayerGB12_Packed,
             PixelType_Gvsp_Coord3D_AC32f,
             PixelType_Gvsp_BayerRG12_Packed,
             PixelType_Gvsp_Coord3D_AB32,
             PixelType_Gvsp_BGR12_Packed,
             PixelType_Gvsp_BayerGR10_Packed,
             PixelType_Gvsp_Coord3D_AC32,
             PixelType_Gvsp_RGB12_Planar,
             PixelType_Gvsp_YCBCR709_422_8,
             PixelType_Gvsp_BGR8_Packed,
             PixelType_Gvsp_Jpeg,
             PixelType_Gvsp_Coord3D_AC32f_64,
             PixelType_Gvsp_YUV422_Packed,
             PixelType_Gvsp_Mono8_Signed,
             PixelType_Gvsp_BayerBG10,
             PixelType_Gvsp_BayerBG16,
             PixelType_Gvsp_BayerGR8,
             PixelType_Gvsp_RGB16_Planar,
             PixelType_Gvsp_Mono4p,
             PixelType_Gvsp_BayerRG10_Packed,
             PixelType_Gvsp_Mono8,
             PixelType_Gvsp_BayerGR16,
             PixelType_Gvsp_BayerGR10,
             PixelType_Gvsp_BGRA8_Packed,
             PixelType_Gvsp_BayerGR12,
             PixelType_Gvsp_Mono12_Packed,
             PixelType_Gvsp_YCBCR709_8_CBYCR,
             PixelType_Gvsp_Coord3D_A32,
             PixelType_Gvsp_YCBCR601_422_8,
             PixelType_Gvsp_Coord3D_C32,
             PixelType_Gvsp_YCBCR411_8_CBYYCRYY,
             PixelType_Gvsp_Undefined,
             PixelType_Gvsp_BayerGR12_Packed,
             PixelType_Gvsp_YCBCR601_411_8_CBYYCRYY,
             PixelType_Gvsp_RGB10_Planar,
             PixelType_Gvsp_BayerGB16,
             PixelType_Gvsp_BayerGB10,
             PixelType_Gvsp_BayerGB12,
             PixelType_Gvsp_BGR565_Packed,
             PixelType_Gvsp_Mono1p,
             PixelType_Gvsp_Coord3D_ABC16,
             PixelType_Gvsp_YUV444_Packed,
             PixelType_Gvsp_YUV422_YUYV_Packed,
             PixelType_Gvsp_BayerBG8,
             PixelType_Gvsp_Coord3D_C32f,
             PixelType_Gvsp_BGR10_Packed,
             PixelType_Gvsp_BayerGB10_Packed,
             PixelType_Gvsp_Coord3D_ABC32f_Planar,
             PixelType_Gvsp_Coord3D_ABC32f,
             PixelType_Gvsp_YCBCR422_8_CBYCRY,
             PixelType_Gvsp_RGB12_Packed,
             PixelType_Gvsp_Mono12,
             PixelType_Gvsp_Mono10,
             PixelType_Gvsp_Mono16,
             PixelType_Gvsp_Mono2p,
             PixelType_Gvsp_Mono14,
             PixelType_Gvsp_RGB10V2_Packed,
             PixelType_Gvsp_RGB12V1_Packed,
             PixelType_Gvsp_Mono10_Packed,
             PixelType_Gvsp_YCBCR601_8_CBYCR,
             PixelType_Gvsp_BayerGB8,
             PixelType_Gvsp_YCBCR8_CBYCR,
             PixelType_Gvsp_RGB565_Packed,
             PixelType_Gvsp_YCBCR601_422_8_CBYCRY

             ]
    return enGvspPixelType in types


# Mono图像转为python数组
def Mono_numpy(data, nWidth, nHeight):
    data_ = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8, offset=0)
    data_mono_arr = data_.reshape(nHeight, nWidth)
    numArray = np.zeros([nHeight, nWidth, 1], "uint8")
    numArray[:, :, 0] = data_mono_arr
    return numArray


# 彩色图像转为python数组
def Color_numpy(data, nWidth, nHeight):
    data_ = np.frombuffer(data, count=int(nWidth * nHeight * 3), dtype=np.uint8, offset=0)
    data_r = data_[0:nWidth * nHeight * 3:3]
    data_g = data_[1:nWidth * nHeight * 3:3]
    data_b = data_[2:nWidth * nHeight * 3:3]

    data_r_arr = data_r.reshape(nHeight, nWidth)
    data_g_arr = data_g.reshape(nHeight, nWidth)
    data_b_arr = data_b.reshape(nHeight, nWidth)
    numArray = np.zeros([nHeight, nWidth, 3], "uint8")

    numArray[:, :, 0] = data_r_arr
    numArray[:, :, 1] = data_g_arr
    numArray[:, :, 2] = data_b_arr
    return numArray


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

    # 开始取图
    def Start_grabbing(self):
        if not self.b_start_grabbing and self.b_open_device:
            self.b_exit = False
            ret = self.obj_cam.MV_CC_StartGrabbing()
            if ret != 0:
                return ret
            self.b_start_grabbing = True
            logger.debug("start grabbing successfully!")
            try:

                self.h_thread_handle = threading.Thread(target=CameraOperation.Work_thread, args=(self,))
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
        stOutFrame = MV_FRAME_OUT()
        memset(byref(stOutFrame), 0, sizeof(stOutFrame))

        while True:
            ret = self.obj_cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
            if 0 == ret:

                # 拷贝图像和图像信息
                if self.buf_save_image is None:
                    self.buf_save_image = (c_ubyte * stOutFrame.stFrameInfo.nFrameLen)()
                self.st_frame_info = stOutFrame.stFrameInfo

                # 获取缓存锁
                self.buf_lock.acquire()
                cdll.msvcrt.memcpy(byref(self.buf_save_image), stOutFrame.pBufAddr, self.st_frame_info.nFrameLen)
                self.buf_lock.release()

                print(f"get one frame: Width[%d], Height[%d], nFrameNum[%d]{datetime.datetime.now()}"
                      % (self.st_frame_info.nWidth, self.st_frame_info.nHeight, self.st_frame_info.nFrameNum))
                # 释放缓存
                self.obj_cam.MV_CC_FreeImageBuffer(stOutFrame)
            else:
                # print("no data, ret = " + To_hex_str(ret))
                continue



            # 是否退出
            if self.b_exit:
                if self.buf_save_image is not None:
                    del self.buf_save_image
                break

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
        try:
            logger.debug("截取图像帧", datetime.datetime.now())
            logger.debug("获取图像帧前的锁状态:", self.buf_lock.locked())
            logger.debug("缓存状态:", self.buf_save_image)

            # 检查 self.st_frame_info 是否已初始化
            if self.st_frame_info is None:
                logger.debug("错误: st_frame_info 未初始化")
                return None

            # 获取锁
            self.buf_lock.acquire()

            # 确保缓冲区已初始化
            if self.buf_save_image is None:
                logger.debug("初始化 buf_save_image")
                self.buf_save_image = (ctypes.c_ubyte * self.st_frame_info.nFrameLen)()  # 分配缓冲区

            if self.buf_save_image is None:
                logger.debug("错误: buf_save_image 为 None", datetime.datetime.now())
                self.buf_lock.release()
                return None

            # 将图像数据复制到缓冲区
            captured_frame_array = np.frombuffer(self.buf_save_image, dtype=np.uint8)
            logger.debug("captured_frame_array", datetime.datetime.now())

            # 获取图像信息
            enGvspPixelType = self.st_frame_info.enPixelType  # 相机对应的像素格式
            nWidth = self.st_frame_info.nWidth  # 图像宽度
            nHeight = self.st_frame_info.nHeight  # 图像高度
            nFrameLen = self.st_frame_info.nFrameLen  # 图像数据长度

            logger.debug(f"图像格式: {enGvspPixelType}, 宽度: {nWidth}, 高度: {nHeight}, 数据长度: {nFrameLen}")


            # 处理彩色图像（Bayer格式或RGB格式）


            if enGvspPixelType == PixelType_Gvsp_BayerGB8:
                # BayerGB8: Bayer格式，需要转换为RGB
                numArray = captured_frame_array.reshape((nHeight, nWidth))
                numArray_rgb = cv2.cvtColor(numArray, cv2.COLOR_BayerGR2RGB)
            elif enGvspPixelType == PixelType_Gvsp_RGB8_Packed:
                logger.debug("处理RGB8彩色图像数据")
                # RGB8: 每个像素占24位（8位R + 8位G + 8位B）
                numArray = captured_frame_array.reshape((nHeight, nWidth, 3))
                numArray_rgb = numArray  # 已经是RGB格式
            elif enGvspPixelType == PixelType_Gvsp_YUV422_Packed:
                # YUV422: 需要转换为RGB
                numArray = captured_frame_array.reshape((nHeight, nWidth, 2))
                numArray_rgb = cv2.cvtColor(numArray, cv2.COLOR_YUV2RGB_Y422)
            else:
                # 其他彩色格式
                numArray = captured_frame_array.reshape((nHeight, nWidth, 3))
                numArray_rgb = numArray

            # 将RGB格式转换为BGR格式
            numArray_bgr = cv2.cvtColor(numArray_rgb, cv2.COLOR_RGB2BGR)
            self.buf_lock.release()
            return numArray_bgr


        except Exception as e:
            logger.debug("异常:", e)
            self.buf_lock.release()
            return None
