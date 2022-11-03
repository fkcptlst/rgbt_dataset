import os
import shutil

dataset_root = 'DATASET_ROOT'
rgb_dir = os.path.join(dataset_root, "sequences", "RGB")
thermal_dir = os.path.join(dataset_root, "sequences", "Thermal")

for i in range(120):
    rgb_filename = os.path.join(rgb_dir, str(i), str(0) + ".jpg")
    thermal_filename = os.path.join(thermal_dir, str(i), str(0) + ".jpg")
    # copy rgb_filename file to './rgb_sample'
    # copy thermal_filename file to './thermal_sample'
    # print(str(rgb_filename))
    # os.system(f'copy {str(rgb_filename)} ./rgb_sample/{i}.jpg')
    # os.system(f'copy {str(thermal_filename)} ./thermal_sample/{i}.jpg')
    shutil.copy(str(rgb_filename), f'./rgb_sample/{i}.jpg')
    shutil.copy(str(thermal_filename), f'./thermal_sample/{i}.jpg')
    print(f'copy {str(rgb_filename)} to ./rgb_sample/{i}.jpg')

