import re
import xml.etree.ElementTree as ET
import traceback
import os
from tqdm import tqdm


def annotation_path_generator(annotations_top_dir):
    """
    generator used for yielding error annotation that end with 'xml.error', that is, the annotation file to be fixed
    :param annotations_top_dir:
    :return:
    """
    top_level_iterator = tqdm(os.listdir(annotations_top_dir), leave=False)
    top_level_iterator.set_description('top level iterator progress: ')
    for annotations_path in top_level_iterator:
        annotations_path = os.path.join(annotations_top_dir, annotations_path)
        # annotation_files_iterator = tqdm(os.listdir(annotations_path))
        # annotation_files_iterator.set_description('annotation files iterator progress: ')
        annotation_files_iterator = os.listdir(annotations_path)
        for annotation_filename in annotation_files_iterator:
            # if not (annotation_filename.endswith(".xml") or annotation_filename.endswith(".xml.error")):
            if not annotation_filename.endswith(".xml"):
                continue
            xml_path = os.path.join(annotations_path, annotation_filename)
            yield xml_path


if __name__ == '__main__':
    error_annotation_path_list = []
    annotations_top_dir = 'annotation'
    new_annotations_top_dir = 'DATASET_ROOT/annotations'
    for i, xml_path in enumerate(annotation_path_generator(annotations_top_dir)):
        # sequence level attributes
        scene_count_dict = {"street": 0, "stadium": 0}
        altitude_count_dict = {"30m": 0, "60m": 0, "90m": 0, "120m": 0}
        illumination_count_dict = {"bright_light": 0, "weak_light": 0}

        new_lines = [""]
        with open(xml_path, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:  # skip the first line
                # scene -----------------------------------------------------
                if line.find('>street<') != -1:
                    scene_count_dict["street"] += 1
                elif line.find('>stadium<') != -1:
                    scene_count_dict["stadium"] += 1
                # altitude --------------------------------------------------
                if line.find('30m') != -1:
                    altitude_count_dict["30m"] += 1
                elif line.find('60m') != -1:
                    altitude_count_dict["60m"] += 1
                elif line.find('90m') != -1:
                    altitude_count_dict["90m"] += 1
                elif line.find('120m') != -1:
                    altitude_count_dict["120m"] += 1
                # illumination ----------------------------------------------
                if line.find('bright_light') != -1:
                    illumination_count_dict["bright_light"] += 1
                elif line.find('weak_light') != -1:
                    illumination_count_dict["weak_light"] += 1

                # remove all <attribute> tags
                # print(re.findall(r'<attribute.*</attribute>', line))
                line = re.sub(r'<attribute.*attribute>', '', line)
                # print(line)
                new_lines.append(line)

        # select the most frequent scene, altitude and illumination
        scene = max(scene_count_dict, key=scene_count_dict.get)
        altitude = max(altitude_count_dict, key=altitude_count_dict.get)
        illumination = max(illumination_count_dict, key=illumination_count_dict.get)

        try:
            # assert that the most frequent scene, altitude and illumination outnumber the others by 80%
            assert scene_count_dict[scene] > 0.8 * sum(scene_count_dict.values()), \
                "xml:{}, scene_count_dict: {}".format(xml_path, scene_count_dict)
            assert altitude_count_dict[altitude] > 0.8 * sum(altitude_count_dict.values()), \
                "xml:{}, altitude_count_dict: {}".format(xml_path, altitude_count_dict)
            assert illumination_count_dict[illumination] > 0.8 * sum(illumination_count_dict.values()), \
                "xml:{}, illumination_count_dict: {}".format(xml_path, illumination_count_dict)
        except AssertionError as e:
            print("\033[1;31m error \033[0m")
            traceback.print_exc()
            # # maually fix the error
            # if xml_path.find("h30_20+\DJI_0004.xml") != -1:  # DJI_0004.xml, stadium
            #     scene = "stadium"
            error_annotation_path_list.append(xml_path)
            pass  # ignore the error

        print("xml:{}, scene: {}, altitude: {}, illumination: {}".format(xml_path, scene, altitude, illumination))
        with open(xml_path, 'r') as f:
            line = f.readline()
            line = re.sub(r'>', f' altitude="{altitude}" scene="{scene}" illumination="{illumination}">', line)
            new_lines[0] = line
        # create a new xml file with the same name
        new_name = f"{i}.xml"
        new_path = os.path.join(new_annotations_top_dir, new_name)
        # create a new xml file with the same name
        with open(new_path, 'w') as f:
            f.writelines(new_lines)
    print("done.")
    print(f"error_annotation_path_list:{error_annotation_path_list}")
