import cv2 as cv
import numpy as np

#视频读取
#cv2.VideoCapture可以捕获摄像头，用数字来控制不同的设备，例如0,1。
#如果是视频文件，直接指定好路径即可。

#VideoCapture()中参数是0，表示打开笔记本的内置摄像头。
#video = cv.VideoCapture(0)

video_path = './video/DJI_0002.mov'
#表示参数是视频文件路径则打开视频
video = cv.VideoCapture(video_path)

#检查是否正确打开isOpened()
#循环读取每一帧
while video.isOpened():
    #video.read() : 一次读取视频中的每一帧，会返回两个值；
    #res : 为bool类型表示这一帧是否真确读取，正确读取为True，如果文件读取到结尾，它的返回值就为False;
    #frame : 表示这一帧的像素点数组
    ret, frame = video.read()
    if frame is None:
        break
    if ret == True:
        cv.imshow("result", frame)
    cv.waitKey(0) # 一次读取一帧，延时1ms，延时为0则表示等待键盘输入，如果输入q则退 出循环
    #100 ： 表示一帧等待一百毫秒在进入下一帧， 0xFF : 表示键入键 27 = esc
    if cv.waitKey(10) & 0xFF == 27:
        break
#video.release()释放视频
video.release()
cv.destroyAllWindows()
