import json
import os.path
import xml.etree.ElementTree as ET


def parse_single_annotation_file(xml_path):
    tree = ET.parse(xml_path)
    # convert xml to dict
    root = tree.getroot()
    xml_dict = {}
    for key, value in root.attrib.items():
        xml_dict[key] = value
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
            # attributes_list = []
            # box_dict['attributes_dict'] = {}  # a dict to store child attributes
            # if box has child attributes, add them to attributes_dict
            # if len(box) > 0:
            #     for attributes in box:
            #         attributes_dict = {'id': int(attributes.attrib['id']), 'value': attributes.text}
            #         attributes_list.append(attributes_dict)
            #     # print(attributes_list)
            #     # sort attributes_list by id
            #     attributes_list.sort(key=lambda x: x['id'])
            #     # assign values to box_dict['attributes_dict'] with keys of "altitude", "illumination", "keep_out", "cam_movement", "scene" accordingly
            #     assert len(attributes_list) == 5, \
            #         f"attributes_list should have 5 elements, got {len(attributes_list)},\n" \
            #         f" attributes_list:{attributes_list},\n" \
            #         f" filename:{xml_path}, \n" \
            #         f"track_id:{track_dict['id']}, \n" \
            #         f"frame:{box_dict['frame']}"
            #
            #     box_dict['attributes_dict']['altitude'] = attributes_list[0]['value']
            #     box_dict['attributes_dict']['illumination'] = attributes_list[1]['value']
            #     box_dict['attributes_dict']['keep_out'] = attributes_list[2]['value']
            #     box_dict['attributes_dict']['cam_movement'] = attributes_list[3]['value']
            #     box_dict['attributes_dict']['scene'] = attributes_list[4]['value']

            track_dict['box_list'].append(box_dict)  # add box_dict to track_dict
        xml_dict['tracks_list'].append(track_dict)

    return xml_dict


if __name__ == '__main__':
    xml_path = os.path.join('DATASET_ROOT', 'annotations', '0.xml')
    xml_dict = parse_single_annotation_file(xml_path)
    # export to json
    json_path = "./XMLAnnotParser.py.test.json"
    with open(json_path, 'w') as f:
        json.dump(xml_dict, f, indent=4)
    print('done')