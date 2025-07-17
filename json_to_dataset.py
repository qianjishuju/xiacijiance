import torch
import torch.utils.data as data
from torch.utils.data import Dataset
from PIL import Image, ImageDraw
import os
import numpy as np
import xml.etree.ElementTree as ET
import logging
import uuid

# 初始化日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

jpgs_path = "/home/lx/文档/hgnetv2-deeplabv3-main/圆识别数据集/VOC2007/JPEGImages"
pngs_path = "/home/lx/文档/hgnetv2-deeplabv3-main/圆识别数据集/VOC2007/SegmentationClass"
classes = ["_background_", "1"]


class CVATDataset(Dataset):
    def __init__(self, xml_file, image_dir, transform=None, target_size=(512, 512)):
        self.xml_file = xml_file
        self.image_dir = image_dir
        self.transform = transform
        self.target_size = target_size

        try:
            self.labels = self.load_label(xml_file)
        except Exception as e:
            logger.error(f"加载标签失败: {e}")
            self.labels = []

        self.image_filenames = [filename for filename in sorted(os.listdir(image_dir)) if
                                filename.lower().endswith(('.png', '.jpg', '.jpeg'))]

    def __len__(self):
        return len(self.image_filenames)

    def __getitem__(self, idx):
        image_path = os.path.join(self.image_dir, self.image_filenames[idx])
        image = Image.open(image_path).convert("RGB")
        label = self.labels[idx]

        # 调整图像和标签的大小
        image = image.resize(self.target_size, Image.LANCZOS)
        label = Image.fromarray(label).resize(self.target_size, Image.NEAREST)
        label = np.array(label, dtype=np.int64)

        if self.transform:
            image = self.transform(image)

        label = torch.tensor(label, dtype=torch.long)  # 将标签转换为 torch.long 类型

        return image, label

    def load_label(self, label_path):
        tree = ET.parse(label_path)
        root = tree.getroot()

        label_data = []
        label_mapping = {}

        label_counter = 1

        for label in root.findall('.//label/name'):
            label_name = label.text
            if label_name not in label_mapping:
                label_mapping[label_name] = label_counter
                label_counter += 1

        for image in root.findall('image'):
            image_id = int(image.get('id'))
            image_name = image.get('name')
            image_width = int(image.get('width'))
            image_height = int(image.get('height'))
            ellipses = image.findall('ellipse')

            label = np.zeros((image_height, image_width), dtype=np.uint8)

            id_mapping = {}

            for ellipse in ellipses:
                label_name = ellipse.get('label')
                ellipse_id = ellipse.get('id') or str(uuid.uuid4())
                if ellipse_id not in id_mapping:
                    id_mapping[ellipse_id] = len(id_mapping) + 1
                label_id = id_mapping[ellipse_id]
                cx = float(ellipse.get('cx'))
                cy = float(ellipse.get('cy'))
                rx = float(ellipse.get('rx'))
                ry = float(ellipse.get('ry'))

                # 在标签上绘制椭圆
                mask = Image.new('L', (image_width, image_height), 0)
                draw = ImageDraw.Draw(mask)
                bbox = [cx - rx, cy - ry, cx + rx, cy + ry]
                draw.ellipse(bbox, fill=1)

                mask_array = np.array(mask, dtype=np.uint8)

                # 将当前椭圆的掩码覆盖在标签上
                label[mask_array > 0] = label_id

            label_data.append(label)

        return label_data


def save_dataset_to_voc_format(dataset, output_dir):
    jpeg_images_dir = jpgs_path
    segmentation_class_dir = pngs_path
    segmentation_dir = os.path.join(output_dir, '/home/lx/文档/hgnetv2-deeplabv3-main/圆识别数据集/VOC2007/ImageSets'
                                                '/Segmentation')

    os.makedirs(jpeg_images_dir, exist_ok=True)
    os.makedirs(segmentation_class_dir, exist_ok=True)
    os.makedirs(segmentation_dir, exist_ok=True)

    file_list_path = os.path.join(segmentation_dir, 'train.txt')

    with open(file_list_path, 'w') as file_list:
        for idx in range(len(dataset)):
            image, label = dataset[idx]
            image_filename = dataset.image_filenames[idx]
            image_basename = os.path.splitext(image_filename)[0]

            image_save_path = os.path.join(jpeg_images_dir, image_filename)
            label_save_path = os.path.join(segmentation_class_dir, f"{image_basename}.png")

            # 保存图像
            try:
                image.save(image_save_path, format='JPEG')
            except Exception as e:
                logger.error(f"保存图像失败 {image_save_path}: {e}")
                continue

            # 转换标签为8位彩色图像并保存
            try:
                label_image = Image.fromarray(label.numpy().astype(np.uint8), mode='P')
                label_image.save(label_save_path, format='PNG')
            except Exception as e:
                logger.error(f"保存标签失败 {label_save_path}: {e}")
                continue

            # 写入文件列表
            file_list.write(f"{image_basename}\n")


if __name__ == '__main__':
    # 使用示例
    xml_file = '/home/lx/下载/YUAN-6-26/annotations.xml'
    image_dir = '/home/lx/下载/YUAN-6-26/images/2'
    output_dir = './'

    # 初始化数据集
    dataset = CVATDataset(xml_file, image_dir)

    # 保存数据集为VOC格式
    save_dataset_to_voc_format(dataset, output_dir)
