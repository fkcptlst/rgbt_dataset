import xml.etree.ElementTree as ET
import os
import cv2
import numpy as np
from XMLAnnotParser import parse_single_annotation_file

config = {
    'step_mode': False,  # if True, step mode, if False, stream mode
    'show_occluded': True,  # if True, show occluded boxes, if False, hide occluded boxes
    'show_outside': False,  # if True, show outside boxes, if False, hide outside boxes
    'display_attributes': True,  # if True, display attributes, if False, hide attributes
    'traverse_mode': True,  # if True, display all vids in the folder, if False, display only one selected vid
    'annot_path': './annotation/h30_5_10/DJI_0002.xml'  # './annotation/h120_20+/DJI_0008.xml',
    # path to annotation file, if traverse_mode is True, this is the folder path
}


def align_rgb_with_thermal(rgb_img, x=-227, y=-50):
    def translate(img, x, y):
        rows, cols, _ = img.shape
        # 平移矩阵m：[[1,0,x],[0,1,y]]
        m = np.float32([[1, 0, x], [0, 1, y]])
        dst = cv2.warpAffine(img, m, (cols, rows))
        return dst

    rgb_img_ = cv2.resize(rgb_img, (0, 0), fx=0.57, fy=0.57, interpolation=cv2.INTER_NEAREST)
    rgb_img_ = translate(rgb_img_, x, y)
    rgb_img_ = rgb_img_[0:512, 0:640]
    return rgb_img_


def visualise(xml_dict, thermal_video, rgb_video):
    # read frame
    frame_idx = 0

    offset = 0
    x = -227
    y = -50

    # frame count
    thermal_frame_count = thermal_video.get(cv2.CAP_PROP_FRAME_COUNT)
    rgb_frame_count = rgb_video.get(cv2.CAP_PROP_FRAME_COUNT)

    # frame rate ratio
    frame_rate_ratio = thermal_video.get(cv2.CAP_PROP_FPS) / rgb_video.get(cv2.CAP_PROP_FPS)
    print(f"frame_rate_ratio: {frame_rate_ratio}")

    while thermal_video.isOpened():
        thermal_video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, thermal_frame = thermal_video.read()

        # get rgb frame according to frame rate ratio
        rgb_frame_idx = int(frame_idx / frame_rate_ratio) + offset
        rgb_video.set(cv2.CAP_PROP_POS_FRAMES, rgb_frame_idx)
        _, rgb_frame = rgb_video.read()
        # align rgb frame
        rgb_frame = align_rgb_with_thermal(rgb_frame, x, y)

        if not ret:
            break
        if thermal_frame is None:
            break
        # print(f'\rframe_idx:{frame_idx}')

        overlapped = cv2.addWeighted(rgb_frame, 0.8, thermal_frame, 0.4, 0)

        for track in xml_dict['tracks_list']:  # get all tracks
            box_list = track['box_list']
            box = box_list[frame_idx]
            assert box['frame'] == str(frame_idx)
            if box['outside'] == '1' and not config['show_outside']:  # skip outside box if not show_occluded
                continue
            if box['occluded'] == '1' and not config['show_occluded']:  # skip occluded box if not show_occluded
                continue
            xtl, ytl, xbr, ybr = int(box['xtl']), int(box['ytl']), int(box['xbr']), int(box['ybr'])
            cv2.rectangle(overlapped, (xtl, ytl), (xbr, ybr), (0, 255, 255), 1)

            font_size = 0.5

            if config['display_attributes']:
                # display occulded info and outside info
                cv2.putText(overlapped, f'occluded:{box["occluded"]}', (xtl, ytl), cv2.FONT_HERSHEY_SIMPLEX,
                            font_size, (0, 0, 255), 1)
                cv2.putText(overlapped, f'outside:{box["outside"]}', (xtl, ytl - 15), cv2.FONT_HERSHEY_SIMPLEX,
                            font_size, (0, 0, 255), 1)
                # # display attributes
                # attributes_dict = box['attributes_dict']
                # if attributes_dict:
                #     for cnt, (key, value) in enumerate(attributes_dict.items()):
                #         cv2.putText(frame, f'{key}:{value}', (xtl, ytl - 15 * (cnt + 2)),
                #                    cv2.FONT_HERSHEY_SIMPLEX,
                #                    font_size,
                #                    (0, 0, 255), 1)
                # else:
                #     cv2.putText(frame, '{}', (xtl, ytl - 15), cv2.FONT_HERSHEY_SIMPLEX, font_size, (0, 0, 255), 1)

            # for box in track['box_list']:
            #     if int(box['frame']) == frame_idx:
            #         # print(box['xtl'], box['ytl'], box['xbr'], box['ybr'])
            #         cv2.rectangle(frame, (int(box['xtl']), int(box['ytl'])), (int(box['xbr']), int(box['ybr'])), (0, 0, 255), 2)
        cv2.imshow(f'vid:{vid_path},   annot:{xml_path}', overlapped)
        if config['step_mode']:
            key = cv2.waitKey(0) & 0xFF
        else:
            key = cv2.waitKey(1) & 0xFF

        # detect key press with non-blocking, if press 'c', continue, if press 's', step mode, if press 'q', quit
        if key == ord('c'):
            config['step_mode'] = False
        elif key == ord('x'):
            config['step_mode'] = True
        elif key == ord('v'):
            config['display_attributes'] = not config['display_attributes']  # verbose
        elif key == ord('1'):
            offset = offset - 1
            print(f'offset:{offset}')
        elif key == ord('2'):
            offset = offset + 1
            print(f'offset:{offset}')
        elif key == ord('w'):
            y = y - 1
            print(f'(x,y):({x},{y})')
        elif key == ord('s'):
            y = y + 1
            print(f'(x,y):({x},{y})')
        elif key == ord('a'):
            x = x - 1
            print(f'(x,y):({x},{y})')
        elif key == ord('d'):
            x = x + 1
            print(f'(x,y):({x},{y})')
        elif key == ord('p'):
            frame_idx = frame_idx - 1
        elif key == ord('q'):
            break
        else:
            frame_idx += 1
    thermal_video.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    # set working directory to current file directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
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
                # rgb video name is vid_path minus 1, e.g. vid_path = 'DJI_0002.mov', rgb_vid_path = 'DJI_0001.mov'
                rgb_vid_path = vid_path[:-5] + str(int(vid_path[-5]) - 1) + '.mov'
                print((f'rgb_vid_path:{rgb_vid_path}'))
                rgb_video = cv2.VideoCapture(rgb_vid_path)
                video = cv2.VideoCapture(vid_path)

                visualise(xml_dict, video, rgb_video)
    else:
        xml_path = config['annot_path']
        xml_dict = parse_single_annotation_file(xml_path)
        vid_path = xml_path.replace('annotation', 'video').replace('xml', 'mov')
        video = cv2.VideoCapture(vid_path)
        visualise(xml_dict, video)

    print('done')
