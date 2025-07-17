# from pathlib import Path
# import sys
# import os
#
# FILE = Path(__file__).resolve()
# ROOT = FILE.parents[0]  # YOLOv5 root directory
# if str(ROOT) not in sys.path:
#     sys.path.append(str(ROOT))  # add ROOT to PATH
#
# ASSETS = ROOT / 'assets'
# # ROOT = Path(os.path.relpath(ROOT, Path.cwd()))
# _WTS_STORAGE_DIR=Path(os.path.expanduser('~'))/ ".lab_model/"
# if not os.path.exists(_WTS_STORAGE_DIR):
#     os.mkdir(_WTS_STORAGE_DIR)
# WTS_STORAGE_DIR=_WTS_STORAGE_DIR
from pathlib import Path
import sys
import os

# 获取当前工作目录作为根目录
ROOT = Path.cwd()

# 将根目录添加到系统路径中
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# 设置 ASSETS 目录
ASSETS = ROOT / 'assets'

# 设置 WTS_STORAGE_DIR 目录在当前用户主目录下的 .lab_model/ 目录
_WTS_STORAGE_DIR = Path(os.path.expanduser('~')) / ".lab_model/"
if not os.path.exists(_WTS_STORAGE_DIR):
    os.mkdir(_WTS_STORAGE_DIR)
WTS_STORAGE_DIR = _WTS_STORAGE_DIR
