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
    for key in dict2:
        if key not in dict1:
            dict1[key] = dict2[key]
        else:
            dict1[key] += dict2[key]
    return dict1


def get_all_dicts(annotations_top_dir):
    """
    get all dicts from all annotation files, notice that this process is time-consuming
    :param annotations_top_dir:
    :return:
    """
    dataset_dict_list = []
    for annotations_path in os.listdir(annotations_top_dir):
        annotations_path = os.path.join(annotations_top_dir, annotations_path)
        for annotation_filename in os.listdir(annotations_path):
            if not annotation_filename.endswith(".xml"):
                continue
            # parse annotation file
            xml_path = os.path.join(annotations_path, annotation_filename)
            xml_dict = parse_single_annotation_file(xml_path)
            dataset_dict_list.append(xml_dict)
    return dataset_dict_list


def count_sequences(annotations_top_dir):
    """
    count how many sequences in the dataset, (only count .xml files under annotations_top_dir)
    :param annotations_top_dir: the top-level dir of annotations
    :return:
    """
    count = 0
    for annotations_path in os.listdir(annotations_top_dir):
        annotations_path = os.path.join(annotations_top_dir, annotations_path)
        for annotation_filename in os.listdir(annotations_path):
            if not annotation_filename.endswith(".xml"):
                continue
            count += 1
    return count

def count_error_files(annotations_top_dir):
    """
    count how many sequences in the dataset, (only count .xml files under annotations_top_dir)
    :param annotations_top_dir: the top-level dir of annotations
    :return:
    """
    count = 0
    for annotations_path in os.listdir(annotations_top_dir):
        annotations_path = os.path.join(annotations_top_dir, annotations_path)
        for annotation_filename in os.listdir(annotations_path):
            if not annotation_filename.endswith(".error"):
                continue
            count += 1
    return count

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


def count_category_occurrences_frame_level_per_sequence(xml_dict):
    """
    count how many times each category appears in a single dataset sequence at frame level, (frame level)
    :param xml_dict:
    :return: category_count_dict: {category_name: count}
    """
    frames_per_track = count_frames_per_track(xml_dict)
    category_count_dict = {}
    for track in xml_dict['tracks_list']:  # for each track
        category = track['label']
        if category not in category_count_dict:
            category_count_dict[category] = frames_per_track[track['id']]
        else:
            category_count_dict[category] += frames_per_track[track['id']]
    return category_count_dict


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
    return sum(frames_count_dict.values())


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


def count_attribute_occurrence_frame_level_per_sequence(xml_dict):
    """
    count how many times each attribute appears in a single dataset sequence at frame level, (frame level)
    :param xml_dict:
    :return: attribute_count_dict: {attribute_id: count}
    """
    # dicts to store the count of each attribute
    outsides_dict = {}  # {outside_or_not: count}
    occlusions_dict = {}  # {occlusion_val: count}
    altitudes_dict = {}  # {altitude_val: count}
    illuminations_dict = {}  # {illumination_val: count}
    keep_outs_dict = {}  # {keep_out_val: count}
    cam_movements_dict = {}  # {cam_movement_val: count}
    scenes_dict = {}  # {scene_val: count}

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

            # process extra attributes
            attributes_dict = box['attributes_dict']
            # print(attributes_dict)
            # if not empty
            if attributes_dict:
                # merge two dicts
                if attributes_dict['altitude'] not in altitudes_dict:
                    altitudes_dict[attributes_dict['altitude']] = 1
                else:
                    altitudes_dict[attributes_dict['altitude']] += 1

                if attributes_dict['illumination'] not in illuminations_dict:
                    illuminations_dict[attributes_dict['illumination']] = 1
                else:
                    illuminations_dict[attributes_dict['illumination']] += 1

                # DEBUG only begin--------------------------------------------------------------
                if attributes_dict['keep_out'] not in keep_outs_dict:
                    if attributes_dict['keep_out'] == 'shake':  #TODO debug
                        # print track id
                        print(f"track id:{track['id']}")
                        # print box id
                        print(f"frame: {box['frame']}")
                        raise Exception('shake')
                # DEBUG only end-----------------------------------------------------------------
                    keep_outs_dict[attributes_dict['keep_out']] = 1
                else:
                    keep_outs_dict[attributes_dict['keep_out']] += 1

                if attributes_dict['cam_movement'] not in cam_movements_dict:
                    cam_movements_dict[attributes_dict['cam_movement']] = 1
                else:
                    cam_movements_dict[attributes_dict['cam_movement']] += 1

                if attributes_dict['scene'] not in scenes_dict:
                    scenes_dict[attributes_dict['scene']] = 1
                else:
                    scenes_dict[attributes_dict['scene']] += 1

    return outsides_dict, occlusions_dict, altitudes_dict, illuminations_dict, keep_outs_dict, cam_movements_dict, scenes_dict


# def count_average_tracks_per_sequence(dataset_dict_list):
#     total_tracks = 0
#     for dataset_dict in dataset_dict_list:
#         total_tracks += len(dataset_dict['tracks_list'])
#     return total_tracks / len(dataset_dict_list)

def annotations_dict_generator(annotations_top_dir):
    """
    generator used for yielding xml dicts
    :param annotations_top_dir:
    :return:
    """
    top_level_iterator = tqdm(os.listdir(annotations_top_dir), leave=False)
    top_level_iterator.set_description('top level iterator progress: ')
    for annotations_path in top_level_iterator:
        annotations_path = os.path.join(annotations_top_dir, annotations_path)
        annotation_files_iterator = tqdm(os.listdir(annotations_path))
        annotation_files_iterator.set_description('annotation files iterator progress: ')
        for annotation_filename in annotation_files_iterator:
            if not annotation_filename.endswith(".xml"):
                continue
            # parse annotation file
            xml_path = os.path.join(annotations_path, annotation_filename)
            try:
                xml_dict = parse_single_annotation_file(xml_path)
            except Exception as e:  # if parsing failed, skip this file, print error, rename the file end with .error
                print("\033[1;31merror\033[0m")  # print bold "error" in red
                # print traceback
                traceback.print_exc()
                # rename xml file to end with .xml.error
                os.rename(xml_path, xml_path + '.error')
                continue
            yield xml_dict, xml_path


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
            shadow=False, startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title(title)
    # plt.savefig(save_path)
    plt.show()
    plt.close()


if __name__ == '__main__':
    annotations_top_dir = './annotation'
    # dataset_dict_list = get_all_dicts(annotations_top_dir)
    count = count_sequences(annotations_top_dir)
    print(count)
