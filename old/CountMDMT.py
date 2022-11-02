import xml.etree.ElementTree as ET
import os
import cv2
import xlsxwriter

if __name__ == '__main__':

    workbook = xlsxwriter.Workbook('新MDMT双机共同ID统计.xlsx')
    # 创建工作表
    worksheet = workbook.add_worksheet()
    data_path = "E:/data/"
    sequences_path = os.path.join(data_path, "MDMT")
    mtsequences = os.listdir(sequences_path)

    image_len = 0
    gt_len = 0

    person_num = 0
    bicycle_num = 0
    vehicle_num = 0
    total_sequences = 2
    person_add = 0
    bicycle_add = 0
    car_add = 0

    for s in range(0, len(mtsequences)):
    # for s in [0]:
        mtsequence = mtsequences[s]
        sequences = os.listdir(os.path.join(sequences_path, mtsequence))
        person_id, bicycle_id, vehicle_id = [], [], []
        for sequence in sequences:
            total_sequences =total_sequences+1
            # print("sequence "+sequence)
            images_path = os.path.join(sequences_path, mtsequence, sequence, 'img1')
            images = os.listdir(images_path)
            legth = len(images)
            image_len += legth

            gt_txt = os.path.join(sequences_path, mtsequence, sequence, 'gt', 'gt.txt')
            with open(gt_txt, 'r') as fr:
                gts = fr.readlines()
            now_person, now_bicycle, now_vehicle = [], [], []
            for gt in gts:
                gt = gt.strip('\n').split(',')
                id = gt[1]
                cls = gt[7]
                assert (cls == '1')or(cls == '2')or(cls == '3')
                if cls == '1' and id not in person_id:
                    person_id.append(id)
                elif cls == '2' and id not in bicycle_id:
                    bicycle_id.append(id)
                elif cls == '3' and id not in vehicle_id:
                    vehicle_id.append(id)
                
                if cls == '1' and id not in now_person:
                    now_person.append(id)
                elif cls == '2' and id not in now_bicycle:
                    now_bicycle.append(id)
                elif cls == '3' and id not in now_vehicle:
                    now_vehicle.append(id)
            gt_len += len(gts)         
            print(sequence,':',len(images),len(gts),len(now_person),len(now_bicycle),len(now_vehicle))
            person_add+=len(now_person)
            bicycle_add+=len(now_bicycle)
            car_add+=len(now_vehicle)
            worksheet.write(total_sequences, 0, sequence)
            worksheet.write(total_sequences, 1, len(images))
            worksheet.write(total_sequences, 2, len(gts))
            worksheet.write(total_sequences, 3, len(now_person))
            worksheet.write(total_sequences, 4, len(now_bicycle))
            worksheet.write(total_sequences, 5, len(now_vehicle))

        person_num += len(person_id)
        bicycle_num += len(bicycle_id)
        vehicle_num += len(vehicle_id)
        print(mtsequence, ':', len(person_id), len(bicycle_id), len(vehicle_id))
    print(person_num, bicycle_num, vehicle_num)
    print(gt_len, image_len)
    worksheet.write(1, 3, person_num)
    worksheet.write(1, 4, bicycle_num)
    worksheet.write(1, 5, vehicle_num)
    worksheet.write(2, 1, image_len)
    worksheet.write(2, 2, gt_len)
    worksheet.write(2, 3, person_add)
    worksheet.write(2, 4, bicycle_add)
    worksheet.write(2, 5, car_add)
    workbook.close()
