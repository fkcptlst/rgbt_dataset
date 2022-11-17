import traceback

from XMLAnnotParser import parse_single_annotation_file
import os
from tqdm import tqdm


def merge_dicts(dict1, dict2):
    """
    merge two dicts by adding values of same keys
    :param dict1:
    :param dict2:
    :return:
    """
    dict3 = {key: dict1[key] for key in dict1}
    for key in dict2:
        if key in dict3:
            dict3[key] += dict2[key]
        else:
            dict3[key] = dict2[key]
    return dict3


# def get_all_dicts(annotations_top_dir):
#     """
#     get all dicts from all annotation files, notice that this process is time-consuming
#     :param annotations_top_dir:
#     :return:
#     """
#     dataset_dict_list = []
#     for annotations_path in os.listdir(annotations_top_dir):
#         annotations_path = os.path.join(annotations_top_dir, annotations_path)
#         for annotation_filename in os.listdir(annotations_path):
#             if not annotation_filename.endswith(".xml"):
#                 continue
#             # parse annotation file
#             xml_path = os.path.join(annotations_path, annotation_filename)
#             xml_dict = parse_single_annotation_file(xml_path)
#             dataset_dict_list.append(xml_dict)
#     return dataset_dict_list


def count_sequences(dataset_root_dir):
    """
    count how many sequences in the dataset, (only count .xml files under annotations_top_dir)
    :param dataset_root_dir: the top-level dir of dataset
    :return:
    """
    return len(os.listdir(os.path.join(dataset_root_dir, "annotations")))


def count_error_files(dataset_root_dir):
    """
    count how many sequences in the dataset, (only count .error files under annotations_top_dir)
    :param dataset_root_dir: the top-level dir of annotations
    :return:
    """
    _count = 0
    for filename in os.listdir(dataset_root_dir):
        if filename.endswith(".error"):
            _count += 1
    return _count


def count_tracks_per_sequence(xml_dict):
    """
    count how many tracks in a single sequence (sequence level)
    :param xml_dict:
    :return:
    """
    assert int(xml_dict['annotations_count']) == len(xml_dict['tracks_list'])  # check if annotations_count is correct
    return int(xml_dict['annotations_count'])


def count_category_occurrences_per_sequence(xml_dict):
    """
    count the occurrence of each category in a single dataset sequence (sequence level)
    :param xml_dict:
    :return: category_count_dict: {category_name: count}, how many times this category appears in the sequence
    """
    category_count_dict = {}
    for track in xml_dict['tracks_list']:
        category = track['label']
        if category not in category_count_dict:
            category_count_dict[category] = 1
        else:
            category_count_dict[category] += 1
    return category_count_dict


def count_category_occurrences_frame_level_per_sequence(xml_dict, count_outside_frames=False):
    """
    count how many times each category appears in a single dataset sequence at frame level, (frame level)
    :param xml_dict:
    :return: category_count_dict: {category_name: count}
    """
    category_count_dict = {}
    if count_outside_frames:
        frames_per_track = count_frames_per_track(xml_dict)
        for track in xml_dict['tracks_list']:  # for each track
            category = track['label']
            if category not in category_count_dict:
                category_count_dict[category] = frames_per_track[track['id']]
            else:
                category_count_dict[category] += frames_per_track[track['id']]
    else:
        for track in xml_dict['tracks_list']:
            category = track['label']
            if category not in category_count_dict:
                category_count_dict[category] = count_non_outside_frames_per_track(track)
            else:
                category_count_dict[category] += count_non_outside_frames_per_track(track)
    return category_count_dict


def count_non_outside_frames_per_track(track):
    """
    count how many frames in a single track are not outside frames
    :param track:
    :return:
    """
    count = 0
    for box in track['box_list']:
        if box['outside'] == '0':
            count += 1
    return count


def count_frames_per_track(xml_dict):
    """
    count how many frames each track has, (track level)
    :param xml_dict:
    :return: frames_per_track: {track_id: frame_count}
    """
    frames_count_dict = {}
    for track in xml_dict['tracks_list']:
        track_id = track['id']
        frames_count_dict[track_id] = len(track['box_list'])
        assert frames_count_dict[track_id] == int(track['box_list'][-1]['frame']) - int(
            track['box_list'][0]['frame']) + 1  # data integrity check, check if the frame count is correct
    return frames_count_dict


def count_frames_per_sequence(xml_dict):
    """
    count how many frames in a single sequence (sequence level)
    :param xml_dict:
    :return: scalar: how many frames in the sequence
    """
    frames_count_dict = count_frames_per_track(xml_dict)
    # check if all tracks have the same frame count
    frame_count_list = list(frames_count_dict.values())
    assert len(
        set(frame_count_list)) == 1  # if all tracks have the same frame count, the set of frame count should have length 1
    return frame_count_list[0]


# def count_attribute_occurrence_per_sequence(xml_dict):
#     """
#     count how many times each attribute appears in a single dataset sequence, (frame level)
#     :param xml_dict:
#     :return:
#     """
#     attribute_count_dict = {}
#     for track in xml_dict['tracks_list']:
#         for box in track['box_list']:
#             attributes_dict = box['attributes_dict']
#             # merge two dicts
#             attribute_count_dict = merge_dicts(attribute_count_dict, attributes_dict)
#     return attribute_count_dict


# def count_attribute_occurrence_frame_level_per_sequence(xml_dict):
#     """
#     count how many times each attribute appears in a single dataset sequence at frame level, (frame level)
#     :param xml_dict:
#     :return: attribute_count_dict: {attribute_id: count}
#     """
#     # dicts to store the count of each attribute
#     outsides_dict = {}  # {outside_or_not: count}
#     occlusions_dict = {}  # {occlusion_val: count}
#     altitudes_dict = {}  # {altitude_val: count}
#     illuminations_dict = {}  # {illumination_val: count}
#     keep_outs_dict = {}  # {keep_out_val: count}
#     cam_movements_dict = {}  # {cam_movement_val: count}
#     scenes_dict = {}  # {scene_val: count}
#
#     for track in xml_dict['tracks_list']:
#         for box in track['box_list']:  # for each frame
#             if box['outside'] not in outsides_dict:
#                 outsides_dict[box['outside']] = 1
#             else:
#                 outsides_dict[box['outside']] += 1
#
#             if box['occluded'] not in occlusions_dict:
#                 occlusions_dict[box['occluded']] = 1
#             else:
#                 occlusions_dict[box['occluded']] += 1
#
#             # process extra attributes
#             attributes_dict = box['attributes_dict']
#             # print(attributes_dict)
#             # if not empty
#             if attributes_dict:
#                 # merge two dicts
#                 if attributes_dict['altitude'] not in altitudes_dict:
#                     altitudes_dict[attributes_dict['altitude']] = 1
#                 else:
#                     altitudes_dict[attributes_dict['altitude']] += 1
#
#                 if attributes_dict['illumination'] not in illuminations_dict:
#                     illuminations_dict[attributes_dict['illumination']] = 1
#                 else:
#                     illuminations_dict[attributes_dict['illumination']] += 1
#
#                 # DEBUG only begin--------------------------------------------------------------
#                 if attributes_dict['keep_out'] not in keep_outs_dict:
#                     if attributes_dict['keep_out'] == 'shake':
#                         # print track id
#                         print(f"track id:{track['id']}")
#                         # print box id
#                         print(f"frame: {box['frame']}")
#                         raise Exception('shake')
#                 # DEBUG only end-----------------------------------------------------------------
#                     keep_outs_dict[attributes_dict['keep_out']] = 1
#                 else:
#                     keep_outs_dict[attributes_dict['keep_out']] += 1
#
#                 if attributes_dict['cam_movement'] not in cam_movements_dict:
#                     cam_movements_dict[attributes_dict['cam_movement']] = 1
#                 else:
#                     cam_movements_dict[attributes_dict['cam_movement']] += 1
#
#                 if attributes_dict['scene'] not in scenes_dict:
#                     scenes_dict[attributes_dict['scene']] = 1
#                 else:
#                     scenes_dict[attributes_dict['scene']] += 1
#
#     return outsides_dict, occlusions_dict, altitudes_dict, illuminations_dict, keep_outs_dict, cam_movements_dict, scenes_dict

def count_attribute_occurrence_frame_level_per_sequence(xml_dict):
    """
    count how many times each attribute appears in a single dataset sequence at frame level, (frame level)
    :param xml_dict:
    :return: attribute_count_dict: {attribute_id: count}
    """
    # dicts to store the count of each attribute
    outsides_dict = {}  # {outside_or_not: count}
    occlusions_dict = {}  # {occlusion_val: count}
    altitudes_dict = {"30m": 0, "60m": 0, "90m": 0, "120m": 0}  # {altitude_val: count}
    illuminations_dict = {"bright_light": 0, "weak_light": 0}  # {illumination_val: count}
    # keep_outs_dict = {}  # {keep_out_val: count}
    # cam_movements_dict = {}  # {cam_movement_val: count}
    scenes_dict = {"street": 0, "stadium": 0}  # {scene_val: count}

    total_frames = count_frames_per_sequence(xml_dict)
    altitudes_dict[xml_dict['altitude']] = total_frames
    illuminations_dict[xml_dict['illumination']] = total_frames
    scenes_dict[xml_dict['scene']] = total_frames

    for track in xml_dict['tracks_list']:
        for box in track['box_list']:  # for each frame
            if box['outside'] not in outsides_dict:
                outsides_dict[box['outside']] = 1
            else:
                outsides_dict[box['outside']] += 1

            if box['occluded'] not in occlusions_dict:
                occlusions_dict[box['occluded']] = 1
            else:
                occlusions_dict[box['occluded']] += 1

            # # process extra attributes
            # attributes_dict = box['attributes_dict']
            # # # print(attributes_dict)
            # # if not empty
            # if attributes_dict:
            #     # merge two dicts
            #     if attributes_dict['altitude'] not in altitudes_dict:
            #         altitudes_dict[attributes_dict['altitude']] = 1
            #     else:
            #         altitudes_dict[attributes_dict['altitude']] += 1
            #
            #     if attributes_dict['illumination'] not in illuminations_dict:
            #         illuminations_dict[attributes_dict['illumination']] = 1
            #     else:
            #         illuminations_dict[attributes_dict['illumination']] += 1

            # # DEBUG only begin--------------------------------------------------------------
            # if attributes_dict['keep_out'] not in keep_outs_dict:
            #     if attributes_dict['keep_out'] == 'shake':
            #         # print track id
            #         print(f"track id:{track['id']}")
            #         # print box id
            #         print(f"frame: {box['frame']}")
            #         raise Exception('shake')
            # # DEBUG only end-----------------------------------------------------------------
            #     keep_outs_dict[attributes_dict['keep_out']] = 1
            # else:
            #     keep_outs_dict[attributes_dict['keep_out']] += 1

            # if attributes_dict['cam_movement'] not in cam_movements_dict:
            #     cam_movements_dict[attributes_dict['cam_movement']] = 1
            # else:
            #     cam_movements_dict[attributes_dict['cam_movement']] += 1
            #
            # if attributes_dict['scene'] not in scenes_dict:
            #     scenes_dict[attributes_dict['scene']] = 1
            # else:
            #     scenes_dict[attributes_dict['scene']] += 1

    return outsides_dict, occlusions_dict, altitudes_dict, illuminations_dict, scenes_dict


def count_attribute_occurrence_frame_level_per_sequence_non_outside(xml_dict):
    """
    count how many times each attribute appears in a single dataset sequence at frame level, (frame level)
    :param xml_dict:
    :return: attribute_count_dict: {attribute_id: count}
    """
    # dicts to store the count of each attribute
    outsides_dict = {}  # {outside_or_not: count}
    occlusions_dict = {}  # {occlusion_val: count}
    altitudes_dict = {"30m": 0, "60m": 0, "90m": 0, "120m": 0}  # {altitude_val: count}
    illuminations_dict = {"bright_light": 0, "weak_light": 0}  # {illumination_val: count}
    # keep_outs_dict = {}  # {keep_out_val: count}
    # cam_movements_dict = {}  # {cam_movement_val: count}
    scenes_dict = {"street": 0, "stadium": 0}  # {scene_val: count}

    total_frames = count_frames_per_sequence(xml_dict)
    altitudes_dict[xml_dict['altitude']] = total_frames
    illuminations_dict[xml_dict['illumination']] = total_frames
    scenes_dict[xml_dict['scene']] = total_frames

    for track in xml_dict['tracks_list']:
        for box in track['non_outside_box_list']:  # for each frame
            if box['outside'] not in outsides_dict:
                outsides_dict[box['outside']] = 1
            else:
                outsides_dict[box['outside']] += 1

            if box['occluded'] not in occlusions_dict:
                occlusions_dict[box['occluded']] = 1
            else:
                occlusions_dict[box['occluded']] += 1

    return outsides_dict, occlusions_dict, altitudes_dict, illuminations_dict, scenes_dict


# def count_average_tracks_per_sequence(dataset_dict_list):
#     total_tracks = 0
#     for dataset_dict in dataset_dict_list:
#         total_tracks += len(dataset_dict['tracks_list'])
#     return total_tracks / len(dataset_dict_list)


def analyze_dataset():
    pass


def draw_pie_chart(data_dict, title):
    """
    draw a pie chart, using data from a dict: data_dict
    :param data_dict: {key: value}
    :param title: title of the chart
    :return:
    """
    # draw a pie chart
    import matplotlib.pyplot as plt
    labels = []
    sizes = []
    for key in data_dict:
        labels.append(key)
        sizes.append(data_dict[key])
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
            shadow=False, startangle=90, colors=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#cc99ff'])
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title(title)
    # plt.savefig(save_path)
    plt.show()
    plt.close()


def draw_bar_chart(data_dict, title):
    """
    draw a bar chart, using data from a dict: data_dict
    """
    import matplotlib.pyplot as plt
    labels = []
    sizes = []
    for key in data_dict:
        labels.append(key)
        sizes.append(data_dict[key])

    fig, ax = plt.subplots(figsize=(10, len(data_dict) / 5))
    ax.barh(labels, sizes)
    ax.set_title(title)

    for i, v in enumerate(sizes):
        ax.text(v + 3, i - 0.25, str(v), fontweight='bold')
    plt.show()
    plt.close()


if __name__ == '__main__':
    dataset_root_dir = 'DATASET_ROOT'
    # dataset_dict_list = get_all_dicts(annotations_top_dir)
    count = count_sequences(dataset_root_dir)
    print(count)
