import xml.etree.ElementTree as ET
import os
import cv2 as cv
from XMLAnnotParser import parse_single_annotation_file

config = {
    'step_mode': False,  # if True, step mode, if False, stream mode
    'show_occluded': True,  # if True, show occluded boxes, if False, hide occluded boxes
    'show_outside': False,  # if True, show outside boxes, if False, hide outside boxes
    'display_attributes': True,  # if True, display attributes, if False, hide attributes
    'traverse_mode': False,  # if True, display all vids in the folder, if False, display only one selected vid
    'annot_path': './annotation/h30_5_10/DJI_0002.xml'  # './annotation/h120_20+/DJI_0008.xml',
    # path to annotation file, if traverse_mode is True, this is the folder path
}


def visualise(xml_dict, video):
    # read frame
    frame_idx = 0
    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break
        if frame is None:
            break
        print(f'frame_idx:{frame_idx}')
        for track in xml_dict['tracks_list']:  # get all tracks
            box_list = track['box_list']
            box = box_list[frame_idx]
            assert box['frame'] == str(frame_idx)
            if box['outside'] == '1' and not config['show_outside']:  # skip outside box if not show_occluded
                continue
            if box['occluded'] == '1' and not config['show_occluded']:  # skip occluded box if not show_occluded
                continue
            xtl, ytl, xbr, ybr = int(box['xtl']), int(box['ytl']), int(box['xbr']), int(box['ybr'])
            cv.rectangle(frame, (xtl, ytl), (xbr, ybr), (0, 255, 255), 1)

            font_size = 0.5

            if config['display_attributes']:
                # display occulded info and outside info
                cv.putText(frame, f'occluded:{box["occluded"]}', (xtl, ytl), cv.FONT_HERSHEY_SIMPLEX,
                           font_size, (0, 0, 255), 1)
                cv.putText(frame, f'outside:{box["outside"]}', (xtl, ytl - 15), cv.FONT_HERSHEY_SIMPLEX,
                           font_size, (0, 0, 255), 1)
                # display attributes
                attributes_dict = box['attributes_dict']
                if attributes_dict:
                    for cnt, (key, value) in enumerate(attributes_dict.items()):
                        cv.putText(frame, f'{key}:{value}', (xtl, ytl - 15 * (cnt + 2)),
                                   cv.FONT_HERSHEY_SIMPLEX,
                                   font_size,
                                   (0, 0, 255), 1)
                else:
                    cv.putText(frame, '{}', (xtl, ytl - 15), cv.FONT_HERSHEY_SIMPLEX, font_size, (0, 0, 255), 1)

            # for box in track['box_list']:
            #     if int(box['frame']) == frame_idx:
            #         # print(box['xtl'], box['ytl'], box['xbr'], box['ybr'])
            #         cv.rectangle(frame, (int(box['xtl']), int(box['ytl'])), (int(box['xbr']), int(box['ybr'])), (0, 0, 255), 2)
        cv.imshow(f'vid:{vid_path},   annot:{xml_path}', frame)
        if config['step_mode']:
            key = cv.waitKey(0) & 0xFF
        else:
            key = cv.waitKey(1) & 0xFF

        # detect key press with non-blocking, if press 'c', continue, if press 's', step mode, if press 'q', quit
        if key == ord('c'):
            config['step_mode'] = False
        elif key == ord('p'):
            config['step_mode'] = True
        elif key == ord('v'):
            config['display_attributes'] = not config['display_attributes']  # verbose
        elif key == ord('q'):
            break
        frame_idx += 1
    video.release()
    cv.destroyAllWindows()


if __name__ == '__main__':
    videos_top_dir = '../video'
    annotations_top_dir = '../annotation'
    if config['traverse_mode']:
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

                visualise(xml_dict, video)
    else:
        xml_path = config['annot_path']
        xml_dict = parse_single_annotation_file(xml_path)
        vid_path = xml_path.replace('annotation', 'video').replace('xml', 'mov')
        video = cv.VideoCapture(vid_path)
        visualise(xml_dict, video)

    print('done')
