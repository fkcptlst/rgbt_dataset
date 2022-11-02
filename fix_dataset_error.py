import re
from dataset_analysis import *


def error_annotation_path_generator(annotations_top_dir):
    """
    generator used for yielding error annotation that end with 'xml.error', that is, the annotation file to be fixed
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
            if not annotation_filename.endswith(".xml.error"):
                continue
            xml_path = os.path.join(annotations_path, annotation_filename)
            yield xml_path


if __name__ == '__main__':
    annotations_top_dir = './annotation'
    for xml_path in error_annotation_path_generator(annotations_top_dir):
        with open(xml_path, 'r') as f:
            lines = f.readlines()
        with open(xml_path, 'w') as f:
            xml_dict = parse_single_annotation_file(xml_path)
            tracks_list = xml_dict['tracks_list']
            bug_count = 0
            cached_track_id = None  # int, used for searching in tracks_list
            cached_box_id = None
            cached_altitude = None  # used for fixing error type 3 below
            for line in lines:
                # update cached_track_id
                raw_cached_track_id = re.findall(r'<track id="\d+">', line)
                if raw_cached_track_id:  # if line contains track id
                    cached_track_id = int(raw_cached_track_id[0].split('"')[1])  # get track id
                    cached_box_id = None
                # update cached_box_id
                raw_cached_box_id = re.findall(r'<box frame="\d+">', line)
                if raw_cached_box_id:  # if line contains box id
                    cached_box_id = int(raw_cached_box_id[0].split('"')[1])  # get box id
                # deal with errors -----------------------------------------------------------------------------------
                # error type 1: keep_out and not_keep_out occur at the same time: auto fix below
                if line.find('>not_keep_out<') != -1 and \
                        line.find('>keep_out<') != -1:  # if both not_keep_out and keep_out exist in the same line
                    # check if all 'outside' of current track are '0'
                    keep_out = True
                    for box in tracks_list[cached_track_id]['box_list']:  # iterate all boxes in current track
                        if box['outside'] != '0':  # if any box is not '0', then keep_out is False
                            keep_out = False
                            break
                    if not keep_out:  # remove keep_out attribute
                        line = re.sub(r'<attribute id="\d+">keep_out</attribute>', '', line)
                    else:  # remove not_keep_out attribute
                        line = re.sub(r'<attribute id="\d+">not_keep_out</attribute>', '', line)
                    bug_count += 1
                # error type 2: shake and not_shake occur at the same time: manually fix
                # error type 3: missing attribute "altitude": auto fix below
                if not re.findall(r'<attribute id="\d+">altitude</attribute>', line):  # if altitude missing
                    if cached_altitude is not None:  # if altitude is cached, insert it into the end of the line
                        line = line[:-2] + cached_altitude + line[-2:]  # notice that the last two characters are '\n'
                        bug_count += 1
                    else:
                        print("\033[1;31merror\033[0m")  # print bold "error" in red
                        print('altitude not cached, need manually fix')  # need manually fix
                        print(f"line:{line}")
                else:  # update cached_altitude
                    cached_altitude = re.findall(r'altitude="(\d+)"', line)[0]
                f.write(line)
        print(f"fixed: {xml_path}, {bug_count} bugs fixed")
        # remove the .error suffix
        os.rename(xml_path, xml_path[:-6])




