import os
from dataset_analysis import *


# %%
def path_generator(dataset_root_dir, dataset_split_list):
    """
    A generator that yields the path of the annotation file, the path of the RGB folder and the path of the thermal folder.
    :param dataset_root_dir:
    :param dataset_split_list: e.g. [0,1,2,3,...]
    :return:
    """
    rgb_top_dir = os.path.join(dataset_root_dir, 'sequences', 'RGB')
    thermal_top_dir = os.path.join(dataset_root_dir, 'sequences', 'Thermal')
    annot_top_dir = os.path.join(dataset_root_dir, 'annotations')

    dataset_split_list_iter = tqdm(dataset_split_list, leave=False)
    dataset_split_list_iter.set_description('progress: ')
    for idx in dataset_split_list_iter:
        idx = int(idx)
        annot_path = os.path.join(annot_top_dir, f'{idx}.xml')
        rgb_dir = os.path.join(rgb_top_dir, f'{idx}')
        thermal_dir = os.path.join(thermal_top_dir, f'{idx}')

        yield idx, annot_path, rgb_dir, thermal_dir


# %%
def annot_dict_generator(dataset_root_dir, dataset_split_list):
    for idx, annot_path, _, _ in path_generator(dataset_root_dir, dataset_split_list):
        _xml_dict = parse_single_annotation_file(annot_path)
        yield idx, _xml_dict, annot_path


# %%
def get_dataset_split_list(split_path):
    with open(split_path, 'r') as f:
        split_list = f.readlines()
        # convert to int
        split_list = [int(x.strip()) for x in split_list]
    return split_list


## ----------------------------------------------------------------------------------------------------------
sequence_info_dict_list = []  # {"idx": int, "frames": int, "categories": Dict, "altitude": str}

for idx, xml_dict, xml_path in annot_dict_generator(dataset_root_dir, dataset_split_list):
    sequence_info_dict = {
        "idx": idx,
        "frames": count_frames_per_sequence(xml_dict),
        "categories": count_category_occurrences_frame_level_per_sequence(xml_dict),
        "altitude": {'30m': 0, '60m': 0, '90m': 0, '120m': 0}
    }
    sequence_info_dict['altitude'][xml_dict['altitude']] = sequence_info_dict['frames']
    sequence_info_dict_list.append(sequence_info_dict)

for i, sequence_info_dict in enumerate(sequence_info_dict_list):
    assert sequence_info_dict['idx'] == i

train_prop = 0.6
val_prop = 0.1
test_prop = 0.3

train_frames_tg = int(total_frames * train_prop + 0.5)  # target train frames
val_frames_tg = int(total_frames * val_prop + 0.5)  # target val frames
test_frames_tg = int(total_frames * test_prop + 0.5)  # target test frames

category_proportion = {}
for category in total_category_distribution_frame_level_dict:
    category_proportion[category] = total_category_distribution_frame_level_dict[category] / total_frames

altitudes_proportion = {}
for altitude in total_altitude_distribution_frame_level_dict:
    altitudes_proportion[altitude] = total_altitude_distribution_frame_level_dict[altitude] / total_frames

tolerance = 0.05  # tolerance

# the target number of frames for each altitude
train_altitude_count_tg = {}
for altitude in altitudes_proportion:
    train_altitude_count_tg[altitude] = int(train_frames_tg * altitudes_proportion[altitude] + 0.5)
val_altitude_count_tg = {}
for altitude in altitudes_proportion:
    val_altitude_count_tg[altitude] = int(val_frames_tg * altitudes_proportion[altitude] + 0.5)
test_altitude_count_tg = {}
for altitude in altitudes_proportion:
    test_altitude_count_tg[altitude] = int(test_frames_tg * altitudes_proportion[altitude] + 0.5)

# the target number of counts for each category
total_category_count = 0
for category in total_category_distribution_frame_level_dict:
    total_category_count += total_category_distribution_frame_level_dict[category]
category_proportion = {}
for category in total_category_distribution_frame_level_dict:
    category_proportion[category] = total_category_distribution_frame_level_dict[category] / total_category_count

train_category_count_tg = {}
for category in category_proportion:
    [category] = int(train_prop * total_category_distribution_frame_level_dict[category] + 0.5)
val_category_count_tg = {}
for category in category_proportion:
    val_category_count_tg[category] = int(val_prop * total_category_distribution_frame_level_dict[category] + 0.5)
test_category_count_tg = {}
for category in category_proportion:
    test_category_count_tg[category] = int(test_prop * total_category_distribution_frame_level_dict[category] + 0.5)

from queue import PriorityQueue

sorted_sequences_dict = dict(sorted(total_sequence_length_distribution.items(), key=lambda x: x[1], reverse=True))

sorted_sequences_idx_list = list(sorted_sequences_dict.keys())  # iterate from longest to shortest
frames_len_list = list(sorted_sequences_dict.values())


# node structure: (['train'|'val'|'test', ...], (train_category_count_dict,val_category_count_dict, test_category_count_dict), (altitude_count_dict)

def heuristic(node, tolerance, train_tg, val_tg, test_tg):
    """
    the heuristic function for A* search, the lower, the better
    """
    train_frames_tg, train_category_count_tg, train_altitude_count_tg = train_tg
    val_frames_tg, val_category_count_tg, val_altitude_count_tg = val_tg
    test_frames_tg, test_category_count_tg, test_altitude_count_tg = test_tg

    node_train_frames, node_val_frames, node_test_frames = node[1]
    node_train_category_count, node_val_category_count, node_test_category_count = node[2]
    node_train_altitude_count, node_val_altitude_count, node_test_altitude_count = node[3]

    # if frames are too much, return inf
    if node_train_frames > train_frames_tg * (1 + tolerance) or node_val_frames > val_frames_tg * (1 + tolerance) \
            or node_test_frames > test_frames_tg * (1 + tolerance):
        return float('inf')

    # if category counts exceed target too much, return inf
    if node_train_category_count > train_category_count_tg * (1 + tolerance) or \
            node_val_category_count > val_category_count_tg * (1 + tolerance) or \
            node_test_category_count > test_category_count_tg * (1 + tolerance):
        return float('inf')

    # if altitude counts exceed target too much, return inf
    if node_train_altitude_count > train_altitude_count_tg * (1 + tolerance) or \
            node_val_altitude_count > val_altitude_count_tg * (1 + tolerance) or \
            node_test_altitude_count > test_altitude_count_tg * (1 + tolerance):
        return float('inf')

    # heuristic
    frames_prop_score = abs(node_train_frames / train_frames_tg - 1) + \
                        abs(node_val_frames / val_frames_tg - 1) + \
                        abs(node_test_frames / test_frames_tg - 1)
    category_prop_score = abs(node_train_category_count / train_category_count_tg - 1) + \
                          abs(node_val_category_count / val_category_count_tg - 1) + \
                          abs(node_test_category_count / test_category_count_tg - 1)
    altitude_prop_score = abs(node_train_altitude_count / train_altitude_count_tg - 1) + \
                          abs(node_val_altitude_count / val_altitude_count_tg - 1) + \
                          abs(node_test_altitude_count / test_altitude_count_tg - 1)

    return frames_prop_score + category_prop_score + altitude_prop_score


# iter order: val, test, train
priority_queue = PriorityQueue()

# first node is val
first_node = (['val'], (0, sequence_info_dict_list[sorted_sequences_idx_list[0]]['frames'], 0),  # frames count
              ({'person': 0, 'cycle': 0, 'car': 0},  # train_category_count_dict
               sequence_info_dict_list[sorted_sequences_idx_list[0]]['categories'],  # val_category_count_dict
               {'person': 0, 'cycle': 0, 'car': 0},),  # test_category_count_dict
              ({'30m': 0, '60m': 0, '90m': 0, '120m': 0},  # train altitude_count_dict
               sequence_info_dict_list[sorted_sequences_idx_list[0]]['altitude'],  # val altitude_count_dict
               {'30m': 0, '60m': 0, '90m': 0, '120m': 0}))  # test altitude_count_dict

priority_queue.put(
    (heuristic(first_node, tolerance, (train_frames_tg, train_category_count_tg, train_altitude_count_tg),
               (val_frames_tg, val_category_count_tg, val_altitude_count_tg),
               (test_frames_tg, test_category_count_tg, test_altitude_count_tg)), first_node))

# A* search
while not priority_queue.empty():
    current_node = priority_queue.get()[1]
    current_split_list = current_node[0]  # ['train'|'val'|'test', ...]
    current_node_train_frames, current_node_val_frames, current_node_test_frames = current_node[1]
    current_node_train_category_count, current_node_val_category_count, current_node_test_category_count = current_node[
        2]
    current_node_train_altitude_count, current_node_val_altitude_count, current_node_test_altitude_count = current_node[
        3]

    # if current node is the last one, break
    if len(current_node[0]) == len(sorted_sequences_idx_list):
        break

    # if current node is not the last one, add next node to priority queue
    next_node_idx = len(current_node[0])
    next_node = (current_split_list + ['val'],
                 (current_node_train_frames, current_node_val_frames + frames_len_list[next_node_idx],
                  current_node_test_frames),
                 (current_node_train_category_count,
                  current_node_val_category_count + sequence_info_dict_list[sorted_sequences_idx_list[next_node_idx]][
                      'categories'], current_node_test_category_count),
                 (current_node_train_altitude_count,
                  current_node_val_altitude_count + sequence_info_dict_list[sorted_sequences_idx_list[next_node_idx]][
                      'altitude'], current_node_test_altitude_count))

    priority_queue.put(
        (heuristic(next_node, tolerance, (train_frames_tg, train_category_count_tg, train_altitude_count_tg),
                   (val_frames_tg, val_category_count_tg, val_altitude_count_tg),
                   (test_frames_tg, test_category_count_tg, test_altitude_count_tg)), next_node))

    next_node = (current_split_list + ['test'],
                 (current_node_train_frames, current_node_val_frames,
                  current_node_test_frames + frames_len_list[next_node_idx]),
                 (current_node_train_category_count, current_node_val_category_count,
                  current_node_test_category_count + sequence_info_dict_list[sorted_sequences_idx_list[next_node_idx]][
                      'categories']),
                 (current_node_train_altitude_count, current_node_val_altitude_count,
                  current_node_test_altitude_count + sequence_info_dict_list[sorted_sequences_idx_list[next_node_idx]][
                      'altitude']))

    priority_queue.put(
        (heuristic(next_node, tolerance, (train_frames_tg, train_category_count_tg, train_altitude_count_tg),
                   (val_frames_tg, val_category_count_tg, val_altitude_count_tg),
                   (test_frames_tg, test_category_count_tg, test_altitude_count_tg)), next_node))

    next_node = (current_split_list + ['train'],
                 (current_node_train_frames + frames_len_list[next_node_idx], current_node_val_frames,
                  current_node_test_frames),
                 (current_node_train_category_count + sequence_info_dict_list[sorted_sequences_idx_list[next_node_idx]][
                     'categories'], current_node_val_category_count, current_node_test_category_count),
                 (current_node_train_altitude_count + sequence_info_dict_list[sorted_sequences_idx_list[next_node_idx]][
                     'altitude'], current_node_val_altitude_count, current_node_test_altitude_count))

    priority_queue.put(
        (heuristic(next_node, tolerance, (train_frames_tg, train_category_count_tg, train_altitude_count_tg),
                     (val_frames_tg, val_category_count_tg, val_altitude_count_tg),
                        (test_frames_tg, test_category_count_tg, test_altitude_count_tg)), next_node))

    print(f'{len(current_split_list)} / 120')

# print result
print(current_node)
