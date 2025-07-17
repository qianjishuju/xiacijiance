import colorsys
import time
import cv2
import numpy as np
import torch
from PIL import Image
from torch import nn
from nets.model.UNet import UNet
from data.process import preprocess_input, resize_image
from utils.utils import show_config
USE_INTEL = False

try:
    import torch_directml

    I_Device = torch_directml.device()
    USE_INTEL = True
except ImportError:
    pass


class Wrapper(object):

    _defaults = {
        "model_path": r"model/yuan_best.pth",
        "num_classes": 2,
        "backbone": "hgnetv2l",
        "input_shape": [512, 512],
        "downsample_factor": 16,
        "mix_type": 0,
        "cuda": True,
        "pp": "aspp",
        "arch": "unet",
    }

    def __init__(self, **kwargs):
        self.num_classes = 2
        kwargs['num_classes'] = 2
        # self.model_path = r"model/yuan_best.pth"
        self.__dict__.update(self._defaults)
        self._defaults.update(kwargs)
        for name, value in kwargs.items():
            setattr(self, name, value)

        if self.num_classes <= 2:
            self.colors = [(0, 0, 0), (128, 0, 0)]
        else:
            hsv_tuples = [(x / self.num_classes, 1., 1.) for x in range(self.num_classes)]
            self.colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
            self.colors = list(map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)), self.colors))
            import random
            random.shuffle(self.colors)

        self.generate()
        show_config(**self._defaults)

    def generate(self, onnx=False):
        # -------------------------------#
        #   载入模型与权值
        # -------------------------------#

        if hasattr(self, "arch") and self.arch.lower() == "unet":
            from nets.model.UNet import UNet
            self.net = UNet(num_classes=self.num_classes, backbone=self.backbone,
                            downsample_factor=self.downsample_factor, pretrained=True, header=self.pp,
                            img_sz=self.input_shape)

        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(device)

        checkpoint = torch.load(self.model_path, map_location=device)
        model_dict = self.net.state_dict()

        # 过滤掉形状不匹配的参数
        pretrained_dict = {k: v for k, v in checkpoint.items() if k in model_dict and model_dict[k].shape == v.shape}
        model_dict.update(pretrained_dict)

        self.net.load_state_dict(model_dict)
        self.net = self.net.eval()

        if hasattr(self.net, "fuse"):
            self.net.fuse()

        print('{} model, and classes loaded.'.format(self.model_path))

        if not onnx:
            if self.cuda:
                self.net = nn.DataParallel(self.net)
                if USE_INTEL:
                    self.net = self.net.to(I_Device)
                else:
                    self.net = self.net.cuda()

    def detect_image(self, image, count=True, name_classes=None):
        # 将图像转换成RGB
        # image = cvtColor(image)

        if name_classes is None:
            name_classes = ["_background_", "1"]
        orininal_h, orininal_w = np.array(image).shape[:2]

        # 图像增加灰条，进行不失真的resize
        image_data, nw, nh = resize_image(image, (self.input_shape[1], self.input_shape[0]))
        image_data = np.expand_dims(np.transpose(preprocess_input(np.array(image_data, np.float32)), (2, 0, 1)), 0)

        with torch.no_grad():
            images = torch.from_numpy(image_data)
            if self.cuda:
                if USE_INTEL:
                    images = images.to(I_Device)
                else:
                    images = images.cuda()

            warmup_data = torch.rand(1, 3, *self.input_shape).to(images.device)
            self.net(warmup_data)

            t = time.time()
            pr = self.net(images)
            pr = pr.argmax(axis=1, keepdim=True)
            pr = pr.to(torch.uint8)
            pr = pr[:, :, int((self.input_shape[0] - nh) // 2): int((self.input_shape[0] - nh) // 2 + nh), \
                 int((self.input_shape[1] - nw) // 2): int((self.input_shape[1] - nw) // 2 + nw)]
            pr = pr.permute(0, 2, 3, 1).cpu().numpy()[0]

            pr = cv2.resize(pr, (orininal_w, orininal_h), interpolation=cv2.INTER_LINEAR)

            seg_img = np.reshape(np.array(self.colors, np.uint8)[np.reshape(pr, [-1])], [orininal_h, orininal_w, -1])
            image1 = Image.fromarray(np.uint8(seg_img))
            image2 = Image.blend(image, image1, 0.7)

            # 新增计算中心点的逻辑
            center_points = []
            for i in range(self.num_classes):
                positions = np.where(pr == i)
                if len(positions[0]) > 0:
                    center_x = int(np.mean(positions[1]))
                    center_y = int(np.mean(positions[0]))
                    center_points.append((center_x, center_y))
                else:
                    center_points.append((None, None))


            if count:
                classes_nums = np.zeros([self.num_classes])
                total_points_num = orininal_h * orininal_w
                print('-' * 63)
                print("|%25s | %15s | %15s|" % ("关键点", "数值", "比例"))
                print('-' * 63)
                for i in range(self.num_classes):
                    num = np.sum(pr == i)
                    ratio = num / total_points_num * 100
                    if num > 0:
                        print("|%25s | %15s | %14.2f%%|" % (str(name_classes[i]), str(num), ratio))
                        print('-' * 63)
                    classes_nums[i] = num
                print("classes_nums:", classes_nums)

            return image2, classes_nums,center_points


def wrapper_yuan(model_path, cuda):
    wrapper = Wrapper(model_path=model_path,
                      num_classes=2,
                      backbone="hgnetv2l",
                      input_shape=[512, 512],
                      downsample_factor=16,
                      mix_type=0,
                      cuda=cuda,
                      pp="aspp")
    return wrapper


if __name__ == "__main__":
    image_path = r"F:\0370数据\2\2\2DK3GVK0327B00008HDCC_PASS_20230617234557_2.jpg"
    image = Image.open(image_path)

    result_image, class_areas ,center_points= wrapper_yuan(r"E:\BasicDemo\瑕疵识别\model\yuan_best.pth", cuda=False).detect_image(
        image)
    array = np.array(class_areas)
    print(array)
    result = array[1:]  # 获取除第一个元素外的所有元素
    sum_result = np.sum(result)  # 计算 result 数组的和
    print(sum_result)
    max_value = np.max(result)  # 计算 result 数组中的最大值
    print(max_value)
    print(center_points)
    result1 = center_points[1]  # 获取除第一个元素外的所有元素
    print(result1)
    result1 = center_points[1]

    if result1 is None:
        print("No valid center point for the class.")
    else:
        center_x, center_y = result1

        r = 260

        # 计算区域的左上角和右下角坐标
        x1 = max(center_x - r, 0)
        y1 = max(center_y - r, 0)
        x2 = min(center_x + r, image.width)
        y2 = min(center_y + r, image.height)
        # 使用PIL的crop方法裁剪图像
        cropped_image = image.crop((x1, y1, x2, y2))
        from 瑕疵识别.异物识别训练代码.yiwu_model_warp import wrapper_yiwu
        # 识别图像
        model = wrapper_yiwu(r"E:\BasicDemo\瑕疵识别\model\yiwu_best.pth", cuda=False)
        result_image, class_areas = model.detect_image(cropped_image)


        # 显示或保存裁剪后的图像
        result_image.show()

    #result_image.show()


