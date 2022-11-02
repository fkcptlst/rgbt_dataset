import os
import csv


if __name__ == '__main__':
    dataset_root = 'F:/multi-drone-mot/data/MDMT'
    train_root = os.path.join(dataset_root, 'train')
    mts = os.listdir(train_root)
    csv_root = os.path.join(dataset_root, 'train_annots.csv')
    fcsv = open(csv_root, 'w', newline="")
    csv_writer = csv.writer(fcsv)
    for mt in mts:
        mt_root = os.path.join(train_root, mt)
        seqs = os.listdir(mt_root)
        for seq in seqs:
            print(seq)
            images_root = os.path.join(mt_root, seq, 'img1')
            images = os.listdir(images_root)
            gt_txt = os.path.join(mt_root, seq, 'gt', 'gt.txt')
            with open(gt_txt, 'r') as fr:
                gts = fr.readlines()
            for image in images:
                for gt in gts:
                    gt = gt.strip('\n').split(',')
                    # print(gt[0], int(image.split('.')[0]))
                    if int(gt[0]) != int(image.split('.')[0]):
                        continue
                    annot = "{0}/{1}/{2}/img1/{3}, {4}, {5}, {6}, {7}, {8}, PeVe".format('train', mt, seq, image, gt[1], gt[2], gt[3], int(gt[2])+int(gt[4])-1, int(gt[3])+int(gt[5])-1)
                    csv_writer.writerow(annot.split(','))



