
import shutil
import os
from typing import *

"""
此模块用于存放文件操作相关的函数
"""

def copy_ttf(from_path): # 将选择的字体文件移动到目标位置
    try:
        shutil.copy(from_path, 'data/fonts/'+from_path.split('/')[-1])
    except:
        pass

def copy_cmd_png(from_path): # 将选择的字体文件移动到目标位置
    try:
        os.makedirs('data/imgs/Background/Custom',exist_ok=True)
        shutil.copy(from_path, 'data/imgs/Background/Custom/'+from_path.split('/')[-1])
    except:
        pass