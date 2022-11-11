import cv2
import os

def get_duration(vid_path):
    cap = cv2.VideoCapture(vid_path)
    # file_path是文件的绝对路径，防止路径中含有中文时报错，需要解码
    if cap.isOpened():  # 当成功打开视频时cap.isOpened()返回True,否则返回False
        # get方法参数按顺序对应下表（从0开始编号)
        rate = cap.get(5)   # 帧速率
        FrameNumber = cap.get(7)  # 视频文件的帧数
        duration = FrameNumber/rate  # 帧速率/视频总帧数 是时间，秒
        return duration

if __name__ == "__main__":
    rgb_vid_path = 'D:\\Project_repository\\RGBT_multi_dataset\\video\\h30_5_10\\DJI_0001.mov'
    thermal_vid_path = 'D:\\Project_repository\\RGBT_multi_dataset\\video\\h30_5_10\\DJI_0002.mov'
    print(f'rgb duration:{get_duration(rgb_vid_path)} s')
    print(f'thermal duration:{get_duration(thermal_vid_path)} s')