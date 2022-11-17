import shutil

from dataset.rgbt import RGBT
import os
import cv2
from tqdm import tqdm
import json
import numpy as np

import hashlib

from copy import deepcopy


# all_dataset = RGBT(root='D:\\Project_repository\\RGBT_multi_dataset\\DATASET_ROOT', image_set='all')
# train_dataset = RGBT(root='D:\\Project_repository\\RGBT_multi_dataset\\DATASET_ROOT', image_set='train')
# val_dataset = RGBT(root='D:\\Project_repository\\RGBT_multi_dataset\\DATASET_ROOT', image_set='val')
# test_dataset = RGBT(root='D:\\Project_repository\\RGBT_multi_dataset\\DATASET_ROOT', image_set='test')


def convert2coco(original_dataset_root, dest_root):
    all_dataset = RGBT(root=original_dataset_root, image_set='all')

    with open(os.path.join(original_dataset_root, 'train.txt'), 'r') as f:
        train_list = f.readlines()
        # convert to int
        train_list = [int(x.strip()) for x in train_list]
    with open(os.path.join(original_dataset_root, 'val.txt'), 'r') as f:
        val_list = f.readlines()
        # convert to int
        val_list = [int(x.strip()) for x in val_list]
    with open(os.path.join(original_dataset_root, 'test.txt'), 'r') as f:
        test_list = f.readlines()
        # convert to int
        test_list = [int(x.strip()) for x in test_list]

    print(f"\ntrain_list: {train_list}")
    print(f"\nval_list: {val_list}")
    print(f"\ntest_list: {test_list}")

    categories = ["car", "person", "cycle"]
    coco_dataset = dict(
        categories=[
            {
                "id": 1,
                "name": "car"
            },
            {
                "id": 2,
                "name": "person"
            },
            {
                "id": 3,
                "name": "cycle"
            }
        ],
        videos=[],  # {id,name,altitude,scene,illumination}
        images=[],  # {id,video_id,frame_id,frame_pos,file_name,height,width}
        annotations=[]  # {id,video_id,image_id,category_id,instance_id,bbox,area,occluded, visibility}
    )
    train_coco_dataset = deepcopy(coco_dataset)
    val_coco_dataset = deepcopy(coco_dataset)
    test_coco_dataset = deepcopy(coco_dataset)

    annot_id = 1
    last_video_id = -1

    for img_id in tqdm(range(len(all_dataset)), leave=False, total=len(all_dataset)):
        """
        annot_dict = {'sequence_id': seq_idx,
                      'instances_count': self.cached_annot_dict['count'],
                      'altitude': self.cached_annot_dict['altitude'],
                      'scene': self.cached_annot_dict['scene'],
                      'illumination': self.cached_annot_dict['illumination'],
                      'frame_id': thermal_frame_idx,
                      'frame_pos': frame_pos,  # position of the frame in the sequence, 0 for first frame, 1 for last frame
                      'track_list': []  # list of track dict
                      }
        track_dict = {'id': track['id'],
                          'label': track['label'],
                          'box': track['box_list'][thermal_frame_idx]  # get box via thermal_frame_idx
                          }
        box_dict = {
                    "frame": 0,
                    "xtl": 137,
                    "ytl": 26,
                    "xbr": 153,
                    "ybr": 65,
                    "outside": 0,
                    "occluded": 0,
                }
        """
        annot_dict = all_dataset.get_annot_dict(img_id)

        video_id = int(annot_dict['sequence_id'])
        video_name = str(video_id) + '.mov'
        altitude = annot_dict['altitude']
        scene = annot_dict['scene']
        illumination = annot_dict['illumination']
        frame_id = annot_dict['frame_id']
        frame_pos = annot_dict['frame_pos']
        file_name = str(img_id).zfill(12) + '.jpg'
        height = 512  # thermal_img.shape[0]
        width = 640  # thermal_img.shape[1]

        # update video info
        if video_id != last_video_id:
            last_video_id = video_id
            video_info = dict(
                id=float(video_id),
                name=video_name,
                width=width,
                height=height,
                altitude=altitude,
                scene=scene,
                illumination=illumination
            )
            if video_id in train_list:
                train_coco_dataset['videos'].append(video_info)
            elif video_id in val_list:
                val_coco_dataset['videos'].append(video_info)
            elif video_id in test_list:
                test_coco_dataset['videos'].append(video_info)
            else:
                raise ValueError('video_id not in train/val/test list')

        # update image info
        image_info = dict(
            id=float(img_id),
            video_id=float(video_id),
            file_name=file_name,
            height=height,
            width=width,
            frame_id=float(frame_id),

            frame_pos=frame_pos,
        )
        if video_id in train_list:
            train_coco_dataset['images'].append(image_info)
        elif video_id in val_list:
            val_coco_dataset['images'].append(image_info)
        elif video_id in test_list:
            test_coco_dataset['images'].append(image_info)
        else:
            raise ValueError('video_id not in train/val/test list')

        # # save image
        # if video_id in train_list:
        #     save_path = os.path.join(dest_root, 'train', file_name)
        # elif video_id in val_list:
        #     save_path = os.path.join(dest_root, 'val', file_name)
        # elif video_id in test_list:
        #     save_path = os.path.join(dest_root, 'test', file_name)
        # else:
        #     raise ValueError('video_id not in train/val/test list')
        # original_img_path = os.path.join(original_dataset_root, 'sequences', 'Thermal', f"{video_id}", f"{frame_id}.jpg")
        # shutil.copy(original_img_path, save_path)

        # update annotations (instances)
        for track in annot_dict['track_list']:
            category_id = categories.index(track['label']) + 1
            instance_id = int(track['id'])

            box_dict = track['box']
            xtl, ytl, xbr, ybr = float(box_dict['xtl']), float(box_dict['ytl']), float(box_dict['xbr']), float(
                box_dict['ybr'])
            bbox = [xtl, ytl, xbr - xtl, ybr - ytl]

            area = (xbr - xtl) * (ybr - ytl)
            occluded = int(box_dict['occluded'])

            if box_dict['outside'] == 1:
                visibility = 0.0
            elif box_dict['occluded'] == 1:
                visibility = 0.1
            else:
                visibility = 1.0

            annotation = dict(
                category_id=float(category_id),
                bbox=bbox,
                area=area,
                iscrowd=0.0,
                visibility=visibility,
                # mot_instance_id=float(instance_id),
                # mot_conf
                # mot_class_id
                id=float(annot_id),
                image_id=float(img_id),
                instance_id=float(instance_id),

                video_id=float(video_id),
                segmentation=[],
                occluded=float(occluded),
            )  # {id,video_id,image_id,category_id,instance_id,bbox,area,occluded, visibility}
            if video_id in train_list:
                train_coco_dataset['annotations'].append(annotation)
            elif video_id in val_list:
                val_coco_dataset['annotations'].append(annotation)
            elif video_id in test_list:
                test_coco_dataset['annotations'].append(annotation)
            else:
                raise ValueError('img_id not in train/val/test list')

            annot_id += 1

    # print dict size
    print('train_coco_dataset size: ', len(train_coco_dataset['images']))
    print('val_coco_dataset size: ', len(val_coco_dataset['images']))
    print('test_coco_dataset size: ', len(test_coco_dataset['images']))

    print('Saving train/val/test json files...')
    # save json
    with open(os.path.join(dest_root, 'annotations', 'train.json'), 'w') as f1:
        json.dump(train_coco_dataset, f1)
    with open(os.path.join(dest_root, 'annotations', 'val.json'), 'w') as f2:
        json.dump(val_coco_dataset, f2)
    with open(os.path.join(dest_root, 'annotations', 'test.json'), 'w') as f3:
        json.dump(test_coco_dataset, f3)
    # calculate md5
    train_hash = hashlib.md5(open(os.path.join(dest_root, 'annotations', 'train.json'), 'rb').read()).hexdigest()
    val_hash = hashlib.md5(open(os.path.join(dest_root, 'annotations', 'val.json'), 'rb').read()).hexdigest()
    test_hash = hashlib.md5(open(os.path.join(dest_root, 'annotations', 'test.json'), 'rb').read()).hexdigest()

    with open(os.path.join(dest_root, 'annotations', 'MD5.txt'), 'w') as f4:
        f4.write(f"train_hash: {train_hash}\n")
        f4.write(f"val_hash: {val_hash}\n")
        f4.write(f"test_hash: {test_hash}\n")

    print('Done')

if __name__ == '__main__':
    convert2coco('DATASET_ROOT', 'COCO_THERMAL')
