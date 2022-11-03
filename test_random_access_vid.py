import cv2
import random

# 读取视频文件
VideoPath = 'D:\\Project_repository\\RGBT_multi_dataset\\video\\h30_5_10\\DJI_0001.mov'
vc = cv2.VideoCapture(VideoPath)  # 读入视频文件

# 获取视频文件总帧数，并产生在总帧数范围内的随机数
NumFrames = int(vc.get(cv2.CAP_PROP_FRAME_COUNT))  # 获取视频的总帧数
n = random.randint(1, NumFrames)  # 生成1~总帧数范围内的一个随机整数

# 按照随机数提取图像，并将图像存放到原视频存放路径，名字以视频文件名命名，后缀为'.jpg'格式
vc.set(cv2.CAP_PROP_POS_FRAMES, n)  # 截取指定帧数
rval, frame = vc.read()  # 分帧读取视频
cv2.imwrite(f'./{n}.jpg', frame)  # 保存图像

# import os
#
# # rename file 1 to 0, 2 to 1, 3 to 2, 4 to 3
# for i in range(1, 121):
#     path_ = os.path.join('DATASET_ROOT', 'sequences', 'RGB', f'{i}')
#     os.rename(path_, os.path.join('DATASET_ROOT', 'sequences', 'RGB', f'{i - 1}'))
