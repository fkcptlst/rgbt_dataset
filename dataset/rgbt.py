import torch
from PIL import Image
from torchvision.datasets import VisionDataset
from typing import Any, Callable, Dict, Optional, Tuple, List
import os
import numpy as np
import cv2 as cv
from AnnotParser import parse_single_annotation_file


def load_image_set_index(image_set_file):
    """
    Load the indexes listed in this dataset's image set file.
    """
    assert os.path.exists(image_set_file), f"Path does not exist: {image_set_file}"
    with open(image_set_file) as f:
        lines = f.readlines()
        image_index_list = [int(x.strip()) for x in lines]
    return image_index_list


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
            # target_transform: Optional[Callable] = None,
            # transforms: Optional[Callable] = None,
    ):
        super(RGBT, self).__init__(root=root, transform=transform)
        self.root = root
        self.image_set = image_set
        assert self.image_set in ["train", "val", "test", "all"], \
            f"image_set must be one of 'train', 'val', 'test', 'all', but got {self.image_set}"
        # self.transforms = transforms
        self.transform = transform
        # self.target_transform = target_transform

        # get frames count from frames_count.csv, format is seq_idx,rgb_frames,thermal_frames
        self.frames_count = np.genfromtxt(os.path.join(self.root, "frames_count.csv"), delimiter=",", dtype=np.int32,
                                          skip_header=1)

        # some info of the dataset
        self.total_seq_num = self.frames_count.shape[0]
        total_thermal_frames = self.frames_count[:, 1].sum()
        total_rgb_frames = self.frames_count[:, 2].sum()
        assert total_thermal_frames == total_rgb_frames
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
        self.img_frames_count = self.frames_count[self._imgs_idx_list, 1]  # list, records frame counts

        # for frame addressing, i.e. locating frame 0/0.jpg requires (seq_idx, frame_idx_offset)
        self.seq_idx_array = np.zeros(self.img_frames_count.sum(), dtype=np.int32)
        self.img_frames_offset_array = np.zeros(self.img_frames_count.sum(), dtype=np.int32)
        # self.img_thermal_frames_offset_array = np.zeros(self.img_frames_count.sum(), dtype=np.int32)

        for i, seq_idx in enumerate(self._imgs_idx_list):
            self.seq_idx_array[
            self.img_frames_count[:i].sum():self.img_frames_count[:i + 1].sum()] = seq_idx
            self.img_frames_offset_array \
                [self.img_frames_count[:i].sum():self.img_frames_count[:i + 1].sum()] \
                = np.arange(self.img_frames_count[i])
            # step = self.img_frames_count[i] / self.img_frames_count[i]
            # self.img_frames_offset_array \
            #     [self.img_frames_count[:i].sum():self.img_frames_count[:i + 1].sum()] \
            #     = np.arange(self.img_frames_count[i], step=step)[:self.img_frames_count[i]]
        # globals for caching
        self.cached_seq_idx = None
        self.cached_annot_dict = None

    def __getitem__(self, index):
        seq_idx = self.seq_idx_array[index]
        rgb_frame_idx = self.img_frames_offset_array[index]
        thermal_frame_idx = self.img_frames_offset_array[index]

        rgb_img = Image.open(os.path.join(self.rgb_dir, f"{seq_idx}", f"{rgb_frame_idx}.jpg"))
        thermal_img = Image.open(os.path.join(self.thermal_dir, f"{seq_idx}", f"{thermal_frame_idx}.jpg"))

        if seq_idx != self.cached_seq_idx:  # if sequence changed, reload annotation
            self.cached_seq_idx = seq_idx
            self.cached_annot_dict = parse_single_annotation_file(os.path.join(self.annotations_dir, f"{seq_idx}.xml"))

        # frame_pos is position of the frame in the sequence, 0 for first frame, 1 for last frame
        frame_pos = thermal_frame_idx / (self.img_frames_count[seq_idx] - 1)
        # extract annotation
        annot_dict = {'sequence_id': seq_idx,
                      'annotations_count': self.cached_annot_dict['count'],
                      'altitude': self.cached_annot_dict['altitude'],
                      'scene': self.cached_annot_dict['scene'],
                      'illumination': self.cached_annot_dict['illumination'],
                      'frame_pos': frame_pos,
                      'track_list': []
                      }
        for track in self.cached_annot_dict['tracks_list']:
            track_dict = {'id': track['id'],
                          'label': track['label'],
                          'box': track['box_list'][thermal_frame_idx]  # get box via thermal_frame_idx
                          }
            annot_dict['track_list'].append(track_dict)

        # apply transform
        if self.transform is not None:
            rgb_img, thermal_img = self.transform(rgb_img, thermal_img)
        return rgb_img, thermal_img, annot_dict

    def __len__(self):
        return self.img_frames_count.sum()


if __name__ == '__main__':
    """
    Test code, visualise dataset
    """
    dataset = RGBT(root='D:\\Project_repository\\RGBT_multi_dataset\\DATASET_ROOT', image_set='all')
    print(f'len: {len(dataset)}')
    step = 5
    i = 0
    while i < len(dataset):
        rgb_img, thermal_img, annot_dict = dataset[i]
        # convert to cv2 RGB image
        rgb_img = cv.cvtColor(np.asarray(rgb_img), cv.COLOR_RGB2BGR)
        thermal_img = cv.cvtColor(np.asarray(thermal_img), cv.COLOR_RGB2BGR)
        assert rgb_img.shape == thermal_img.shape
        # print(f'annot_dict: {annot_dict}')

        overlapped = cv.addWeighted(rgb_img, 0.8, thermal_img, 0.4, 0)
        seq_id, altitude, scene, illumination, frame_pos = \
            annot_dict['sequence_id'], annot_dict['altitude'], annot_dict['scene'], \
            annot_dict['illumination'], annot_dict['frame_pos']
        cv.putText(overlapped, f'altitude:{altitude}', (0, 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv.putText(overlapped, f'scene:{scene}', (0, 30), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv.putText(overlapped, f'illumination:{illumination}', (0, 45), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv.putText(overlapped, f'frame_pos:{frame_pos}', (0, 60), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv.putText(overlapped, f'seq_id:{seq_id}', (0, 75), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        for track in annot_dict['track_list']:
            box = track['box']
            if box['outside'] == '0':  # skip outside box
                xtl, ytl, xbr, ybr = int(box['xtl']), int(box['ytl']), int(box['xbr']), int(box['ybr'])
                cv.putText(overlapped, f'id:{track["id"]}', (xtl, ytl - 15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255),
                           1)
                cv.putText(overlapped, f'id:{track["label"]}', (xtl, ytl - 30), cv.FONT_HERSHEY_SIMPLEX, 0.5,
                           (0, 0, 255), 1)
                cv.rectangle(overlapped, (xtl, ytl), (xbr, ybr), (0, 255, 255), 1)
        # display
        cv.imshow("overlapping", overlapped)
        key = cv.waitKey(0) & 0xFF
        if key == ord('f'):
            step += 5
            print(f'step: {step}')
        elif key == ord('s'):
            step = max(1, step - 5)
            print(f'step: {step}')
        elif key == ord('p'):
            i = max(0, i - step * 2)
        i += step
