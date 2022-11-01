import xml.etree.ElementTree as ET
import os
import cv2 as cv


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
    videos_top_dir = './video'
    annotations_top_dir = './annotation'
    for annotations_path in os.listdir(annotations_top_dir):
        videos_path = os.path.join(videos_top_dir, annotations_path)
        annotations_path = os.path.join(annotations_top_dir, annotations_path)
        # if videos_path not exist, skip
        if not os.path.exists(videos_path):
            continue
        for annotation_filename in os.listdir(annotations_path):
            if not annotation_filename.endswith(".xml"):
                continue
            filename_without_suffix = annotation_filename.split('.')[0]
            video_filename = filename_without_suffix + '.mov'
            if not video_filename in os.listdir(videos_path):
                continue

            # parse annotation file
            xml_path = os.path.join(annotations_path, annotation_filename)
            xml_dict = parse_single_annotation_file(xml_path)

            # read video
            vid_path = os.path.join(videos_path, video_filename)
            video = cv.VideoCapture(vid_path)

            # read frame
            frame_idx = 0
            while video.isOpened():
                ret, frame = video.read()
                if not ret:
                    break
                if frame is None:
                    break
                print(f'frame_idx:{frame_idx}')
                for track in xml_dict['tracks_list']: # get all tracks
                    box_list = track['box_list']
                    box = box_list[frame_idx]
                    assert box['frame'] == str(frame_idx)
                    if box['outside'] == '1':  # skip outside box
                        continue
                    xtl, ytl, xbr, ybr = int(box['xtl']), int(box['ytl']), int(box['xbr']), int(box['ybr'])
                    cv.rectangle(frame, (xtl, ytl), (xbr, ybr), (0, 0, 255), 1)

                    # for box in track['box_list']:
                    #     if int(box['frame']) == frame_idx:
                    #         # print(box['xtl'], box['ytl'], box['xbr'], box['ybr'])
                    #         cv.rectangle(frame, (int(box['xtl']), int(box['ytl'])), (int(box['xbr']), int(box['ybr'])), (0, 0, 255), 2)
                cv.imshow('frame', frame)
                cv.waitKey(1)
                frame_idx += 1






