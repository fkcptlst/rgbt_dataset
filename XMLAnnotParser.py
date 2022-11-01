import xml.etree.ElementTree as ET

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