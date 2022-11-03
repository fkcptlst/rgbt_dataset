import cv2
import os

from tqdm import tqdm


def convert(vid_file_path, img_dir_path):
    vidcap = cv2.VideoCapture(vid_file_path)
    # get frame count
    frame_count = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    iterator = tqdm(range(frame_count), leave=False)
    iterator.set_description(f'vid: {vid_file_path}, img: {img_dir_path}')
    for count, _ in enumerate(iterator):
        success, image = vidcap.read()
        if success:
            cv2.imwrite(os.path.join(img_dir_path, f"{count}.jpg"), image)
            count += 1
    vidcap.release()
    return frame_count


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


checkpoint_idx = 0  # checkpoint is file that is not done

thermal_frames_count_list = []
rgb_frames_count_list = []
log_list = [f'checkpoint_idx: {checkpoint_idx}']

if __name__ == '__main__':
    # convert('video/h30_5_10/DJI_0001.mov', 'images')

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
            rgb_frames = convert(rgb_vid_path, rgb_img_dir)

            thermal_frames_count_list.append(thermal_frames)
            rgb_frames_count_list.append(rgb_frames)
        except Exception as e:
            print(e)
            log_list.append(e)
    # export to csv
    import pandas as pd

    df = pd.DataFrame({'thermal': thermal_frames_count_list, 'rgb': rgb_frames_count_list})
    df.to_csv('frames_count.csv', index=True)

    with open('convert_vid_to_img.py.log', 'w') as f:
        f.writelines(log_list)
    print('Done')
