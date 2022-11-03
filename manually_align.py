import cv2
import os
import numpy as np

RGB_path = os.path.join('DATASET_ROOT', 'sequences', 'RGB', '0', '0.jpg')
thermal_path = os.path.join('DATASET_ROOT', 'sequences', 'Thermal', '0', '0.jpg')

rgb_img = cv2.imread(RGB_path)
t_img = cv2.imread(thermal_path)

h_t, w_t, _ = t_img.shape
h_rgb, w_rgb, _ = rgb_img.shape


def translate(img, x, y):
    rows, cols, _ = img.shape
    # 平移矩阵M：[[1,0,x],[0,1,y]]
    M = np.float32([[1, 0, x], [0, 1, y]])
    dst = cv2.warpAffine(img, M, (cols, rows))
    return dst


def align_rgb_with_thermal(rgb_img):
    def translate(img, x, y):
        rows, cols, _ = img.shape
        # 平移矩阵M：[[1,0,x],[0,1,y]]
        M = np.float32([[1, 0, x], [0, 1, y]])
        dst = cv2.warpAffine(img, M, (cols, rows))
        return dst
    rgb_img1 = cv2.resize(rgb_img, (0, 0), fx=0.57, fy=0.57, interpolation=cv2.INTER_NEAREST)
    rgb_img2 = translate(rgb_img1, x=-227, y=-50)
    rgb_img3 = rgb_img2[0:512, 0:640]
    return rgb_img3


print(f"h_t: {h_t}, w_t: {w_t}")
x, y = -227, -50
while True:
    rgb_img1 = cv2.resize(rgb_img, (0, 0), fx=0.57, fy=0.57,
                          interpolation=cv2.INTER_NEAREST)
    rgb_img2 = translate(rgb_img1, x, y)
    rgb_img3 = rgb_img2[0:h_t, 0:w_t]
    # 权重越大，透明度越低
    overlapping = cv2.addWeighted(rgb_img3, 0.8, t_img, 0.6, 0)
    # display
    cv2.imshow("overlapping", overlapping)
    key = cv2.waitKey(0) & 0xFF
    if key == ord('w'):
        y -= 1
    elif key == ord('s'):
        y += 1
    elif key == ord('a'):
        x -= 1
    elif key == ord('d'):
        x += 1
    print(f'x{x},y{y}')  # best: x-227,y-50
    continue
