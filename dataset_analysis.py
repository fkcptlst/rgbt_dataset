from XMLAnnotParser import parse_single_annotation_file
import os


def merge_dicts(dict1, dict2):
    """
    merge two dicts
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
    for track in xml_dict['tracks_list']:
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


def count_attribute_occurrence_per_sequence(xml_dict):
    """
    count how many times each attribute appears in a single dataset sequence, (frame level)
    :param xml_dict:
    :return:
    """
    attribute_count_dict = {}
    for track in xml_dict['tracks_list']:
        for box in track['box_list']:
            for attributes in box['attributes_list']:
                attribute = attributes['id']
                if attribute not in attribute_count_dict:
                    attribute_count_dict[attribute] = 1
                else:
                    attribute_count_dict[attribute] += 1
    return attribute_count_dict


def count_attribute_occurrence_frame_level_per_sequence(xml_dict):
    """
    count how many times each attribute appears in a single dataset sequence at frame level, (frame level)
    :param xml_dict:
    :return: attribute_count_dict: {attribute_id: count}
    """
    frames_per_track = count_frames_per_track(xml_dict)
    attribute_count_dict = {}
    for track in xml_dict['tracks_list']:
        for box in track['box_list']:
            for attributes in box['attributes_list']:
                attribute = attributes['id']
                if attribute not in attribute_count_dict:
                    attribute_count_dict[attribute] = frames_per_track[track['id']]
                else:
                    attribute_count_dict[attribute] += frames_per_track[track['id']]
    return attribute_count_dict


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
    for annotations_path in os.listdir(annotations_top_dir):
        annotations_path = os.path.join(annotations_top_dir, annotations_path)
        for annotation_filename in os.listdir(annotations_path):
            if not annotation_filename.endswith(".xml"):
                continue
            # parse annotation file
            xml_path = os.path.join(annotations_path, annotation_filename)
            xml_dict = parse_single_annotation_file(xml_path)
            yield xml_dict


def analyze_dataset():
    pass


def draw_pie_chart(data_dict, title):
    """
    draw a pie chart, using data from a dict: data_dict
    :param data_dict:
    :param title:
    :param save_path:
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
