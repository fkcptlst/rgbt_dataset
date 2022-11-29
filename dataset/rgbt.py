import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
import random
from PIL import Image
from torchvision.datasets import VisionDataset
from torchvision.transforms import transforms
from typing import Any, Callable, Dict, Optional, Tuple, List
import os
import numpy as np
import cv2

if __name__ == '__main__':
    from AnnotParser import parse_single_annotation_file
else:
    from .AnnotParser import parse_single_annotation_file


# TODO bug here, path error, if run this file single, it will should be AnnotParser.parse_single_annotation_file
# however, if Dataset is used in other file, it should be .AnnotParser.parse_single_annotation_file, with dot


def load_image_set_index(image_set_file):
    """
    Load the indexes listed in this dataset's image set file.
    """
    assert os.path.exists(image_set_file), f"Path does not exist: {image_set_file}"
    with open(image_set_file) as f:
        lines = f.readlines()
        image_index_list = [int(x.strip()) for x in lines]
    return image_index_list


def align_rgb_with_thermal(rgb_img):
    def translate(img, x, y):
        rows, cols, _ = img.shape
        # 平移矩阵m：[[1,0,x],[0,1,y]]
        m = np.float32([[1, 0, x], [0, 1, y]])
        dst = cv2.warpAffine(img, m, (cols, rows))
        return dst

    rgb_img_ = cv2.resize(rgb_img, (0, 0), fx=0.57, fy=0.57, interpolation=cv2.INTER_NEAREST)
    rgb_img_ = translate(rgb_img_, x=-227, y=-50)
    rgb_img_ = rgb_img_[0:512, 0:640]
    return rgb_img_


class RGBT(VisionDataset):
    """
    Dataset Class for RGBT dataset
    Args:
        root (string): Root directory of the RGBT Dataset.
        image_set (string, optional): Select the image_set to use, ``"train"``, ``"val"`` or ``"test"``.
        transform (callable, optional): A function/transform that  takes in an PIL image
            and returns a transformed version. E.g, ``transforms.RandomCrop``
        target_transform (callable, required): A function/transform that takes in the
            target and transforms it.
        transforms (callable, optional): A function/transform that takes input sample and its target as entry
            and returns a transformed version.

        .. note::
        :attr:`transforms` and the combination of :attr:`transform` and :attr:`target_transform` are mutually exclusive.
    """

    def __init__(
            self,
            root: str,
            image_set: str = "train",
            transform: Optional[Callable] = None,
            online: bool = True,
            supplementary_rgb_num: int = 0,
            # 0: no rgb, 1: if online, only display current and previous frame, if online=False, display previous, current and next frame
            # target_transform: Optional[Callable] = None,
            # transforms: Optional[Callable] = None,
    ):
        super(RGBT, self).__init__(root=root, transform=transform)
        self.root = root
        self.image_set = image_set
        assert self.image_set in {"train", "val", "test", "all"}, \
            f"image_set must be one of 'train', 'val', 'test', 'all', but got {self.image_set}"

        self.supplementary_rgb_num = supplementary_rgb_num
        self.online = online

        # self.transforms = transforms
        self.transform = transform
        # self.target_transform = target_transform

        # get frames count from frames_count.csv, format is seq_idx,rgb_frames,thermal_frames
        self.total_frames_count = np.genfromtxt(os.path.join(self.root, "frames_count.csv"), delimiter=",",
                                                dtype=np.int32,
                                                skip_header=1)

        # some info of the dataset
        self.total_seq_num = self.total_frames_count.shape[0]
        total_thermal_frames = self.total_frames_count[:, 1].sum()
        total_rgb_frames = self.total_frames_count[:, 2].sum()
        # assert total_thermal_frames == total_rgb_frames
        self.total_frames = total_thermal_frames

        self.annotations_dir = os.path.join(self.root, "annotations")

        self.rgb_dir = os.path.join(self.root, "sequences", "RGB")
        self.thermal_dir = os.path.join(self.root, "sequences", "Thermal")

        if self.image_set == "train":
            self._imgs_idx_list = load_image_set_index(os.path.join(self.root, "train.txt"))
        elif self.image_set == "val":
            self._imgs_idx_list = load_image_set_index(os.path.join(self.root, "val.txt"))
        elif self.image_set == "test":
            self._imgs_idx_list = load_image_set_index(os.path.join(self.root, "test.txt"))
        elif self.image_set == "all":
            self._imgs_idx_list = load_image_set_index(os.path.join(self.root, "all.txt"))

        # some count of current image set, depends on image_set
        self.img_seq_num = len(self._imgs_idx_list)
        # self.img_thermal_frames_count = self.frames_count[self._imgs_idx_list, 1]  # list, records frame counts
        # self.img_rgb_frames_count = self.frames_count[self._imgs_idx_list, 2]  # list, records frame counts
        self.img_frames_count = self.total_frames_count[self._imgs_idx_list]  # list, records frame counts
        self.img_thermal_frames_count = self.total_frames_count[self._imgs_idx_list, 1]  # list, records frame counts
        self.img_rgb_frames_count = self.total_frames_count[self._imgs_idx_list, 2]  # list, records frame counts

        # for frame addressing, i.e. locating frame 0/0.jpg requires (seq_idx, frame_idx_offset)
        self.seq_idx_array = np.zeros(self.img_thermal_frames_count.sum(), dtype=np.int32)
        self.img_frames_offset_array = np.zeros(self.img_thermal_frames_count.sum(),
                                                dtype=np.int32)  # offset of each thermal frame

        self.rgb_thermal_frame_ratios = self.img_rgb_frames_count / self.img_thermal_frames_count  # array, records frame rate ratios

        # self.img_thermal_frames_offset_array = np.zeros(self.img_thermal_frames_count.sum(), dtype=np.int32)

        for i, seq_idx in enumerate(self._imgs_idx_list):
            self.seq_idx_array \
                [self.img_thermal_frames_count[:i].sum():self.img_thermal_frames_count[:i + 1].sum()] \
                = seq_idx  # seq_idx_array records sequence idx of each thermal frame
            self.img_frames_offset_array \
                [self.img_thermal_frames_count[:i].sum():self.img_thermal_frames_count[:i + 1].sum()] \
                = np.arange(self.img_thermal_frames_count[i])
            # img_frames_offset_array records offset of each thermal frame, i.e. the frame idx of each thermal frame

            # step = self.img_thermal_frames_count[i] / self.img_thermal_frames_count[i]
            # self.img_frames_offset_array \
            #     [self.img_thermal_frames_count[:i].sum():self.img_thermal_frames_count[:i + 1].sum()] \
            #     = np.arange(self.img_thermal_frames_count[i], step=step)[:self.img_thermal_frames_count[i]]
        # globals for caching
        self.cached_seq_idx = None
        self.cached_annot_dict = None

    def __getitem__(self, index):
        seq_idx = self.seq_idx_array[index]
        rgb_frame_idx = min(int(self.img_frames_offset_array[index] * self.rgb_thermal_frame_ratios[seq_idx] + 0.5),
                            self.img_rgb_frames_count[seq_idx] - 1)  # round to the nearest int, prevent out of range
        thermal_frame_idx = self.img_frames_offset_array[index]

        rgb_img = Image.open(os.path.join(self.rgb_dir, f"{seq_idx}", f"{rgb_frame_idx}.jpg"))
        thermal_img = Image.open(os.path.join(self.thermal_dir, f"{seq_idx}", f"{thermal_frame_idx}.jpg"))

        # weakly aligned
        rgb_img = align_rgb_with_thermal(np.array(rgb_img))
        rgb_img = Image.fromarray(rgb_img)

        if seq_idx != self.cached_seq_idx:  # if sequence changed, reload annotation
            self.cached_seq_idx = seq_idx
            self.cached_annot_dict = parse_single_annotation_file(os.path.join(self.annotations_dir, f"{seq_idx}.xml"))

        # frame_pos is position of the frame in the sequence, 0 for first frame, 1 for last frame
        frame_pos = round(thermal_frame_idx / (self.img_thermal_frames_count[seq_idx] - 1), 4)  # keep 4 decimal places
        # extract annotation
        annot_dict = {'sequence_id': seq_idx,
                      'instances_count': self.cached_annot_dict['count'],
                      'altitude': self.cached_annot_dict['altitude'],
                      'scene': self.cached_annot_dict['scene'],
                      'illumination': self.cached_annot_dict['illumination'],
                      'frame_id': thermal_frame_idx,
                      'frame_pos': frame_pos,
                      # position of the frame in the sequence, 0 for first frame, 1 for last frame
                      'track_list': []  # list of track dict
                      }
        for track in self.cached_annot_dict['tracks_list']:
            track_dict = {'id': track['id'],
                          'label': track['label'],
                          'box': track['box_list'][thermal_frame_idx]  # get box via thermal_frame_idx
                          }
            annot_dict['track_list'].append(track_dict)

        rgb_img_dict = {'0': rgb_img}
        for i in range(1, self.supplementary_rgb_num + 1):
            rgb_frame_idx = max(
                min(int(self.img_frames_offset_array[index] * self.rgb_thermal_frame_ratios[seq_idx] + 0.5) - i,
                    self.img_rgb_frames_count[seq_idx] - 1), 0)  # prevent out of range, larger than 0, smaller than max
            supplementary_rgb_img = Image.open(os.path.join(self.rgb_dir, f"{seq_idx}", f"{rgb_frame_idx}.jpg"))
            supplementary_rgb_img = align_rgb_with_thermal(np.array(supplementary_rgb_img))
            supplementary_rgb_img = Image.fromarray(supplementary_rgb_img)
            rgb_img_dict[f"-{i}"] = supplementary_rgb_img
            if not self.online:
                rgb_frame_idx_ = min(
                    int(self.img_frames_offset_array[index] * self.rgb_thermal_frame_ratios[seq_idx] + 0.5) + i,
                    self.img_rgb_frames_count[seq_idx] - 1)
                supplementary_rgb_img_ = Image.open(os.path.join(self.rgb_dir, f"{seq_idx}", f"{rgb_frame_idx_}.jpg"))
                supplementary_rgb_img_ = align_rgb_with_thermal(np.array(supplementary_rgb_img_))
                supplementary_rgb_img_ = Image.fromarray(supplementary_rgb_img_)
                rgb_img_dict[f"+{i}"] = supplementary_rgb_img_

        # apply transform
        if self.transform is not None:
            thermal_img = self.transform(thermal_img)
            for key, value in rgb_img_dict.items():
                rgb_img_dict[key] = self.transform(value)

        # if rgb_img and thermal_img are PIL.Image, convert to tensor
        for key, value in rgb_img_dict.items():
            if isinstance(value, Image.Image):
                rgb_img_dict[key] = transforms.ToTensor()(value)
        if isinstance(thermal_img, Image.Image):
            thermal_img = transforms.ToTensor()(thermal_img)

        return annot_dict, thermal_img, rgb_img_dict

    def __len__(self):
        return self.img_thermal_frames_count.sum()

    def get_annot_dict(self, index):
        seq_idx = self.seq_idx_array[index]
        rgb_frame_idx = min(int(self.img_frames_offset_array[index] * self.rgb_thermal_frame_ratios[seq_idx] + 0.5),
                            self.img_rgb_frames_count[seq_idx] - 1)  # round to the nearest int, prevent out of range
        thermal_frame_idx = self.img_frames_offset_array[index]

        # rgb_img = Image.open(os.path.join(self.rgb_dir, f"{seq_idx}", f"{rgb_frame_idx}.jpg"))
        # thermal_img = Image.open(os.path.join(self.thermal_dir, f"{seq_idx}", f"{thermal_frame_idx}.jpg"))

        # weakly aligned
        # rgb_img = align_rgb_with_thermal(np.array(rgb_img))
        # rgb_img = Image.fromarray(rgb_img)

        if seq_idx != self.cached_seq_idx:  # if sequence changed, reload annotation
            self.cached_seq_idx = seq_idx
            self.cached_annot_dict = parse_single_annotation_file(os.path.join(self.annotations_dir, f"{seq_idx}.xml"))

        # frame_pos is position of the frame in the sequence, 0 for first frame, 1 for last frame
        frame_pos = round(thermal_frame_idx / (self.img_thermal_frames_count[seq_idx] - 1), 4)  # keep 4 decimal places
        # extract annotation
        annot_dict = {'sequence_id': seq_idx,
                      'instances_count': self.cached_annot_dict['count'],
                      'altitude': self.cached_annot_dict['altitude'],
                      'scene': self.cached_annot_dict['scene'],
                      'illumination': self.cached_annot_dict['illumination'],
                      'frame_id': thermal_frame_idx,
                      'frame_pos': frame_pos,
                      # position of the frame in the sequence, 0 for first frame, 1 for last frame
                      'track_list': []  # list of track dict
                      }
        for track in self.cached_annot_dict['tracks_list']:
            track_dict = {'id': track['id'],
                          'label': track['label'],
                          'box': track['box_list'][thermal_frame_idx]  # get box via thermal_frame_idx
                          }
            annot_dict['track_list'].append(track_dict)

        return annot_dict


if __name__ == '__main__':
    """
    Test code, visualise dataset
    """
    # test_loader = DataLoader(
    #     dataset=RGBT(root='D:\\Project_repository\\RGBT_multi_dataset\\DATASET_ROOT', online=False,
    #                  supplementary_rgb_num=2, image_set='all'),
    #     batch_size=5,
    #     shuffle=False,
    #     num_workers=0,
    #     # pin_memory=True,
    #     # drop_last=False,
    # )  # TODO some bug in annot, annot not aligned. solution: convert to COCO-VID format
    # for i, (annot, thermal, rgb_dict) in enumerate(test_loader):
    #     if i < 530:
    #         continue
    #     print(f"i: {i}, annot: {annot}, thermal shape: ({thermal.shape})")
    #     for key, value in rgb_dict.items():
    #         print(f"key: {key}, value shape: ({value.shape})")
    #     # # export to json
    #     # import json
    #     # with open('D:\\Project_repository\\RGBT_multi_dataset\\DATASET_ROOT\\test.json', 'w') as f:
    #     #     json.dump(annot, f)
    #     # print(annot)
    #     if i > 545:
    #         break

    dataset = RGBT(root='D:\\Project_repository\\RGBT_multi_dataset\\DATASET_ROOT', online=False,
                   supplementary_rgb_num=0, image_set='all')
    print(f'len: {len(dataset)}')
    annot, thermal, rgb_dict = dataset[0]
    print(f"annot: {annot}, thermal shape: ({thermal.shape})")
    step = 20
    i = 0

    sampled = np.zeros((len(dataset),))
    while i < len(dataset):
        # generate a random index
        # j = random.randint(0, 200)
        # annot_dict, thermal_img, rgb_dict = dataset[min(i + j, len(dataset) - 1)]
        annot_dict, thermal_img, rgb_dict = dataset[i]
        # rgb_img = rgb_dict['0']
        # convert to cv2 RGB image
        # rgb_img = cv2.cvtColor(np.asarray(rgb_img), cv2.COLOR_RGB2BGR)
        # thermal_img = cv2.cvtColor(np.asarray(thermal_img), cv2.COLOR_RGB2BGR)
        # convert tensor to cv2 RGB image
        # rgb_img = cv2.cvtColor(np.asarray(rgb_img.permute(1, 2, 0)), cv2.COLOR_RGB2BGR)
        thermal_img = cv2.cvtColor(np.asarray(thermal_img.permute(1, 2, 0)), cv2.COLOR_RGB2BGR)
        # assert rgb_img.shape == thermal_img.shape
        # print(f'annot_dict: {annot_dict}')

        # overlapped = cv2.addWeighted(rgb_img, 0.8, thermal_img, 0.4, 0)
        overlapped = thermal_img
        seq_id, altitude, scene, illumination, frame_pos = \
            annot_dict['sequence_id'], annot_dict['altitude'], annot_dict['scene'], \
            annot_dict['illumination'], annot_dict['frame_pos']
        cv2.putText(overlapped, f'altitude:{altitude}', (0, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(overlapped, f'scene:{scene}', (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(overlapped, f'illumination:{illumination}', (0, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(overlapped, f'frame_pos:{frame_pos}', (0, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(overlapped, f'seq_id:{seq_id}', (0, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # if sampled[seq_id] < 2:
        #     sampled[seq_id] += 1
        # else:
        #     print(f'skip seq_id: {seq_id}, i={i}')
        #     i += step

        for track in annot_dict['track_list']:
            box = track['box']
            if box['outside'] == '0':  # skip outside box
                xtl, ytl, xbr, ybr = int(box['xtl']), int(box['ytl']), int(box['xbr']), int(box['ybr'])
                cv2.putText(overlapped, f'id:{track["id"]}', (xtl, ytl - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 0, 255),
                            1)
                cv2.putText(overlapped, f'id:{track["label"]}', (xtl, ytl - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 0, 255), 1)
                cv2.rectangle(overlapped, (xtl, ytl), (xbr, ybr), (0, 255, 255), 1)
        # display
        cv2.imshow("overlapping", overlapped)
        # save image
        # if not os.path.exists(f'D:\\Project_repository\\RGBT_multi_dataset\\samples'):
        #     # create dir
        #     os.makedirs(f'D:\\Project_repository\\RGBT_multi_dataset\\samples')
        overlapped = overlapped * 255
        # cv2.imwrite(f'D:\\Project_repository\\RGBT_multi_dataset\\samples\\{seq_id}-{int(sampled[seq_id])}.jpg', overlapped)
        # if all sampled, break
        # if np.sum(sampled) == 2 * len(dataset):
        #     break
        key = cv2.waitKey(1) & 0xFF
        if key == ord('f'):
            step += 5
            print(f'step: {step}')
        elif key == ord('s'):
            step = max(1, step - 5)
            print(f'step: {step}')
        elif key == ord('p'):
            i = max(0, i - step * 2)
        i += step
