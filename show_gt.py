import os
import cv2
import xml.etree.ElementTree as ET

if __name__ == '__main__':
    data_path = "E:/data/MDMT/"
    mtsequences = os.listdir(data_path)
    print(mtsequences)
    for s in range(0, len(mtsequences)):
    # for s in [2]:
        mtsequence = mtsequences[s]
        sequences = os.listdir(os.path.join(data_path, mtsequence))
        for sequence in sequences:
            # if sequence != '27-1':
            #     continue
            print(sequence)
            images_path = os.path.join(data_path, mtsequence, sequence, 'img1')
            gt_path = os.path.join(data_path, mtsequence, sequence, 'gt', 'gt.txt')
            images = os.listdir(images_path)
            with open(gt_path, 'r') as f:
                gts = f.readlines()
            for i in range(0, len(images)):
                # print(i)
                image = images[i]
                # img = cv2.imread(os.path.join(images_path, image))
                for gt in gts:
                    gt = gt.strip('\n').split(',')
                    frame = int(gt[0])
                    assert frame <= len(images)
                    if frame != i+1:
                        continue
                    id = gt[1]
                    x1 = int(gt[2])
                    y1 = int(gt[3])
                    x2 = int(gt[2]) + int(gt[4])
                    y2 = int(gt[3]) + int(gt[5])
                    cls = int(gt[7])
                    # cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    # cv2.putText(img, id, (x1, y2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 2)
                # img = cv2.resize(img, (1080, 720))
                # cv2.imshow("image", img)
                # cv2.waitKey(1)
