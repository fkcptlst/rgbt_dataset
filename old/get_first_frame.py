import xml.etree.ElementTree as ET
import os
import cv2
import shutil

if __name__ == '__main__':

    data_path = "F:/multi-drone-mot/data"
    sequences_path = os.path.join(data_path, "MDMT", 'train')
    new_images_path = "F:/multi-drone-mot/data/first_frame"
    mtsequences = os.listdir(sequences_path)

    for s in range(0, len(mtsequences)):
        mtsequence = mtsequences[s]
        sequences = os.listdir(os.path.join(sequences_path, mtsequence))
        person_id, bicycle_id, vehicle_id = [], [], []
        for sequence in sequences:
            # print(sequence)
            images_path = os.path.join(sequences_path, mtsequence, sequence, 'img1')
            first_image = os.path.join(images_path, '000001.jpg')
            new_image = os.path.join(new_images_path, sequence + '.jpg')
            shutil.copy(first_image, new_image)

