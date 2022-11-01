import json
import xml.etree.ElementTree as ET
import os
import cv2
from PIL import Image, ImageDraw, ImageFont

def parse_single_annotation_file(xml_path):
    tree = ET.parse(xml_path)
    # convert xml to dict
    root = tree.getroot()
    xml_dict = {}
    xml_dict['annotations_count'] = root.attrib['count']
    xml_dict['tracks_list'] = []
    for track in root:  # get all tracks
        # copy track.attrib to track_dict to avoid changing track.attrib, result is like {'id': '0', 'label': 'person'}
        track_dict = {}
        for key, value in track.attrib.items():
            track_dict[key] = value
        # print(box.attrib)
        track_dict['box_list'] = []
        for box in track:  # get all boxes
            box_dict = {}
            for key, value in box.attrib.items():
                box_dict[key] = value
            box_dict['attributes_list'] = []  # a list to store child attributes
            for attributes in box:
                attributes_dict = {}
                for key, value in attributes.attrib.items():
                    attributes_dict[key] = value
                attributes_dict['value'] = attributes.text
                box_dict['attributes_list'].append(attributes_dict)
            track_dict['box_list'].append(box_dict)
        xml_dict['tracks_list'].append(track_dict)

    return xml_dict


if __name__ == '__main__':
    ann_path = "./annotation"
    for filename in os.listdir(ann_path):
        if not filename.endswith(".xml"):
            continue
        xml_path = os.path.join(ann_path, filename)
        object = parse_single_annotation_file(xml_path)
        # export object to a json file
        # with open(os.path.join(annotations_path, annotation_filename.split('.')[0] + '.json'), 'w') as f:
        #     json.dump(object, f)
        print(object['annotations_count'])
        for track in object['tracks_list']:
            print(track['id'])
            print(track['label'])
            for box in track['box_list']:
                print(box['xtl'], box['ytl'], box['xbr'], box['ybr'])
                for attributes in box['attributes_list']:
                    print(attributes['id'], attributes['value'])

#
# def parse_rec(annotation_filename):
#     tree = ET.parse(annotation_filename)  # 解析读取xml函数
#     objects = []
#     img_dir = []
#     for xml_name in tree.findall('annotation_filename'):
#         img_path = os.path.join(pic_path, xml_name.text)
#         img_dir.append(img_path)
#     for obj in tree.findall('object'):
#         obj_struct = {}
#         obj_struct['name'] = obj.find('name').text
#         obj_struct['pose'] = obj.find('pose').text
#         obj_struct['truncated'] = int(obj.find('truncated').text)
#         obj_struct['difficult'] = int(obj.find('difficult').text)
#         bbox = obj.find('bndbox')
#         obj_struct['bbox'] = [int(bbox.find('xmin').text),
#                               int(bbox.find('ymin').text),
#                               int(bbox.find('xmax').text),
#                               int(bbox.find('ymax').text)]
#         objects.append(obj_struct)
#
#     return objects, img_dir
#
#
# # 可视化
# def visualise_gt(objects, img_dir):
#     for id, img_path in enumerate(img_dir):
#         img = Image.open(img_path)
#         draw = ImageDraw.Draw(img)
#         for a in objects:
#             xmin = int(a['bbox'][0])
#             ymin = int(a['bbox'][1])
#             xmax = int(a['bbox'][2])
#             ymax = int(a['bbox'][3])
#             label = a['name']
#             draw.rectangle((xmin, ymin, xmax, ymax), fill=None, outline=(0, 255, 0), width=2)
#             draw.text((xmin - 10, ymin - 15), label, fill=(0, 255, 0), font=font)  # 利用ImageDraw的内置函数，在图片上写入文字
#         img.show()
#
#
# fontPath = "C:\Windows\Fonts\Consolas\consola.ttf"  # 字体路径
# root = 'F:/dataset/AQM'
# annotations_path = os.path.join(root, 'Annotations')  # xml文件所在路径
# pic_path = os.path.join(root, 'JPEGImages')  # 样本图片路径
# font = ImageFont.truetype(fontPath, 16)
#
# for annotation_filename in os.listdir(annotations_path):
#     xml_path = os.path.join(annotations_path, annotation_filename)
#     object, img_dir = parse_rec(xml_path)
#     visualise_gt(object, img_dir)
