import os
import numpy as np
import cv2
from tqdm import tqdm
import traceback

dataset_root = 'DATASET_ROOT'


def file_exists(filename):
    return os.path.isfile(filename)


log_list = []

"""
check list:
- seq num is 119
- frames number count equal to .csv file
- all files exists
- all seq frames > 0
- thermal shape is (512, 640, 3)
- rgb shape is (1080, 1920, 3)
- xml exists
- frames in xml equals to thermal img number
"""

if __name__ == '__main__':
    # register keybord interrupt, write log to file
    def keyboard_interrupt_handler(signal, frame):
        print('KeyboardInterrupt (ID: {}) has been caught. Writing log...'.format(signal))
        with open(os.path.join(dataset_root, "data_integrity_check.log"), 'w') as f:
            for log in log_list:
                f.write(log)
        exit(0)
    import signal
    signal.signal(signal.SIGINT, keyboard_interrupt_handler)

    try:
        frames_count = np.genfromtxt(os.path.join(dataset_root, "frames_count.csv"), delimiter=",",
                                     dtype=np.int32, skip_header=1)
        total_seq_num = frames_count.shape[0]
        # # assert rgb_frames_count equals thermal_frames_count
        # assert (frames_count[:, 1] == frames_count[:, 2]).all(), f'rgb_frames_count != thermal_frames_count, ' \
        #                                                          f'frames_count[:, 1]:{frames_count[:, 1]}, ' \
        #                                                          f'frames_count[:, 2]:{frames_count[:, 2]}'
        # assert total_seq_num is 120
        assert total_seq_num == 120, f'total_seq_num is {total_seq_num}, not 120'
        for i in tqdm(range(total_seq_num)):
            try:
                rgb_dir = os.path.join(dataset_root, "sequences", "RGB", str(i))
                thermal_dir = os.path.join(dataset_root, "sequences", "Thermal", str(i))
                rgb_frames_count = frames_count[i, 1]
                thermal_frames_count = frames_count[i, 2]

                rgb_files_count = len(os.listdir(rgb_dir))
                thermal_files_count = len(os.listdir(thermal_dir))

                # assert rgb_frames_count equals rgb_files_count
                assert rgb_frames_count == rgb_files_count, f'rgb_frames_count != rgb_files_count,' \
                                                            f'rgb_dir:{rgb_dir},' \
                                                            f'rgb_frames_count:{rgb_frames_count},' \
                                                            f'rgb_files_count:{rgb_files_count}'

                # assert thermal_frames_count equals thermal_files_count
                assert thermal_frames_count == thermal_files_count, f'thermal_frames_count != thermal_files_count, ' \
                                                                    f'thermal_dir:{thermal_dir}, ' \
                                                                    f'thermal_frames_count:{thermal_frames_count}, ' \
                                                                    f'thermal_files_count:{thermal_files_count}'
                # assert rgb_frames_count == thermal_frames_count, f'rgb_frames_count != thermal_frames_count, ' \
                #                                                  f'rgb_dir:{rgb_dir}, rgb_frames_count:{rgb_frames_count}, ' \
                #                                                  f'thermal_dir:{thermal_dir}, thermal_frames_count:{thermal_frames_count}'
                assert rgb_frames_count > 0, f'rgb_frames_count <= 0, rgb_dir:{rgb_dir}, rgb_frames_count:{rgb_frames_count}'
                assert thermal_frames_count > 0, f'thermal_frames_count <= 0, thermal_dir:{thermal_dir}, thermal_frames_count:{thermal_frames_count}'
            except Exception as e:
                traceback.print_exc()
                log_list.append(f'Error in seq {i}: {e}')
            for j in range(rgb_frames_count):
                try:
                    rgb_filename = os.path.join(rgb_dir, str(j) + ".jpg")
                    assert file_exists(rgb_filename), f'rgb_filename:{rgb_filename} not exists'
                    thermal_filename = os.path.join(thermal_dir, str(j) + ".jpg")
                    assert file_exists(thermal_filename), f'thermal_filename:{thermal_filename} not exists'
                    rgb_img = cv2.imread(rgb_filename)
                    thermal_img = cv2.imread(thermal_filename)
                    assert rgb_img.shape == \
                           (1080, 1920, 3), f'rgb_filename:{rgb_filename}: rgb_img.shape:{rgb_img.shape} not (1080, 1920, 3)'
                    assert thermal_img.shape == \
                           (512, 640, 3), f'thermal_filename:{thermal_filename}: ' \
                                          f'thermal_img.shape:{thermal_img.shape} not (512, 640, 3)'
                except Exception as e:
                    print(e)
                    traceback.print_exc()
                    log_list.append(f'{str(e)}\n')
        for i in range(total_seq_num):
            try:
                xml_path = os.path.join(dataset_root, "annotations", str(i) + ".xml")
                assert file_exists(xml_path), f'xml_path:{xml_path} not exists'
            except Exception as e:
                print(e)
                log_list.append(f'{str(e)}\n')
    except Exception as e:
        print(e)
        log_list.append(f'{str(e)}\n')
    with open(os.path.join(dataset_root, "data_integrity_check.log"), 'w') as f:
        f.writelines(log_list)
        if len(log_list) == 0:
            print("data integrity check pass")
            f.write("\ndata integrity check pass")
        else:
            print("data integrity check failed")
            f.write("\ndata integrity check failed")
