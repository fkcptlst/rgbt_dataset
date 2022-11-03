import cv2
import os
import numpy as np

from tqdm import tqdm
import traceback


def align_rgb_with_thermal(rgb_img):
    def translate(img, x, y):
        rows, cols, _ = img.shape
        # 平移矩阵m：[[1,0,x],[0,1,y]]
        m = np.float32([[1, 0, x], [0, 1, y]])
        dst = cv2.warpAffine(img, m, (cols, rows))
        return dst

    rgb_img1 = cv2.resize(rgb_img, (0, 0), fx=0.57, fy=0.57, interpolation=cv2.INTER_NEAREST)
    rgb_img2 = translate(rgb_img1, x=-227, y=-50)
    rgb_img3 = rgb_img2[0:512, 0:640]
    return rgb_img3


def convert(vid_file_path, img_dir_path, term=None):
    """

    :param vid_file_path:
    :param img_dir_path:
    :param step:
    :param term: if not None: frame count must equal to term
    :return:
    """
    vidcap = cv2.VideoCapture(vid_file_path)
    # get frame count
    total_frame_count = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    count = 0  # count of frames actually extracted

    if term is None:
        step = 1
    else:
        step = total_frame_count / (term + 1)

    if total_frame_count == 0:
        raise ValueError(f'frame count is 0 for {vid_file_path}')
    range_list = [int(i) for i in range(total_frame_count)]
    iterator = tqdm(range_list, leave=False)
    iterator.set_description(f'vid: {vid_file_path}, img: {img_dir_path}')
    for n in iterator:
        success, image = vidcap.read()
        if success and n >= step * count:
            if term is not None:  # align rgb with thermal
                image = align_rgb_with_thermal(image)
            cv2.imwrite(os.path.join(img_dir_path, f'{count}.jpg'), image)
            count += 1
            if count == term and abs(range_list[-1] - step * count) <= 5:
                break  # if reached terminal and remaining less than 5 frames
    vidcap.release()
    if term is not None:
        assert count == term, f"vid{vid_file_path}, img:{img_dir_path}, count:{count}, term:{term}"
    return int(count)


def video_path_generator(annot_top_dir):
    """
    use old annot_top_dir to generate video path
    :param annot_top_dir:
    :return: idx, thermal_vid_path, rgb_vid_path
    """
    idx = -1  # so that the first video will be 0
    top_level_iterator = tqdm(os.listdir(annot_top_dir), leave=False)
    top_level_iterator.set_description('top level iterator progress: ')
    for annot_dir in top_level_iterator:
        annots_path = os.path.join(annot_top_dir, annot_dir)
        for annot_filename in os.listdir(annots_path):
            video_filename = os.path.splitext(annot_filename)[0] + '.mov'
            if not video_filename.endswith(".mov"):
                continue
            # videos_path is annots_path changed 'annotation' to 'video'
            thermal_vid_path = os.path.join(annots_path.replace('annotation', 'video'), video_filename)
            # get last 4 digits of video filename
            thermal_idx = int(video_filename[-8:-4])
            rgb_idx = thermal_idx - 1
            rgb_vid_path = thermal_vid_path.replace(f'{thermal_idx:04d}', f'{rgb_idx:04d}')
            idx += 1
            yield idx, thermal_vid_path, rgb_vid_path


checkpoint_idx = 77  # checkpoint is file that is not done
only = True  # if True, only convert the checkpoint file
no_error = True

thermal_frames_count_list = []
rgb_frames_count_list = []
log_list = [f'checkpoint_idx: {checkpoint_idx}']

if __name__ == '__main__':
    image_top_dir = os.path.join('./DATASET_ROOT', 'sequences')
    for idx, thermal_vid_path, rgb_vid_path in video_path_generator('annotation'):
        if idx < checkpoint_idx:
            continue
        try:
            thermal_img_dir = os.path.join(image_top_dir, 'Thermal', f'{idx}')
            rgb_img_dir = os.path.join(image_top_dir, 'RGB', f'{idx}')

            print(f'\nidx: {idx}, thermal_vid_path: {thermal_vid_path}, rgb_vid_path: {rgb_vid_path}')
            log_list.append(f'\nidx: {idx}, thermal_vid_path: {thermal_vid_path}, rgb_vid_path: {rgb_vid_path}')

            os.makedirs(thermal_img_dir, exist_ok=True)
            os.makedirs(rgb_img_dir, exist_ok=True)

            thermal_frames = convert(thermal_vid_path, thermal_img_dir)
            rgb_frames = convert(rgb_vid_path, rgb_img_dir, term=thermal_frames)

            assert thermal_frames == rgb_frames, f'\nidx: {idx}, thermal_vid_path: {thermal_vid_path}, rgb_vid_path: {rgb_vid_path},' \
                                                 f'thermal_frames:{thermal_frames},rgb_frames:{rgb_frames} unmatch'

            thermal_frames_count_list.append(thermal_frames)
            rgb_frames_count_list.append(rgb_frames)
            print(f"idx:{idx}, thermal_frames:{thermal_frames}, rgb_frames:{rgb_frames}")
        except Exception as e:
            no_error = False
            print(e)
            traceback.print_exc()
            log_list.append(str(e))
        if only:
            break
    # export to csv
    import pandas as pd

    df = pd.DataFrame({'thermal': thermal_frames_count_list, 'rgb': rgb_frames_count_list})
    df.to_csv(os.path.join('./DATASET_ROOT', 'frames_count.csv'), index=True)

    with open('convert_vid_to_img.py.log', 'w') as f:
        f.writelines(log_list)
    print('Done')
    if no_error:
        print('No exception occurred')
    else:
        print('Error occurred')
#
#     # NOTICE: some data fix below, not necessary to run
#     path_dict = {
#         # '44': 'video/h30_20+/DJI_0014.mov',
#         # '61': 'video/h60_10_20/DJI_0012.mov',
#         # '64': 'video/h60_10_20/DJI_0070.mov',
#         # '86': 'video/h60_5_10/DJI_0234.mov',
#         '101': 'video/h90_20+/DJI_0003.mov',  # broken video
#         # '108': 'video/h90_20+/DJI_0428.mov',
#         # '110': 'video/h90_5_10/DJI_0018.mov',
#     }
#     for idx, path in path_dict.items():
#         convert(path, os.path.join('./DATASET_ROOT', 'sequences', 'RGB', idx))
# # 44, \h30_20+\DJI_0015.xml
# # 61, \h60_10_20\DJI_0013.xml
# # 64, \h60_10_20\DJI_0071.xml
# # 86, \h60_5_10\DJI_0235.xml
# # 101, \h90_20+\DJI_0004.xml
# # 108, \h90_20+\DJI_0429.xml
# # 110, \h90_5_10\DJI_0019.xml
