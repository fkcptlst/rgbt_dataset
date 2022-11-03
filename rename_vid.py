"""
Used for renaming video files
"""
import os
from tqdm import tqdm


def annotation_path_generator(annotations_top_dir):
    """
    generator used for yielding error annotation that end with 'xml.error', that is, the annotation file to be fixed
    :param annotations_top_dir: using OLD annotation directory, because old annotations match the old video files
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
    annotations_top_dir = 'annotation'
    new_video_top_dir = 'new_video'
    for i, xml_path in enumerate(annotation_path_generator(annotations_top_dir)):
        video_path = xml_path.replace('annotation', 'video')
        video_path = video_path.replace('.xml', '.mov')
        new_video_path = os.path.join(new_video_top_dir, f'{i}.mov')
        os.rename(video_path, new_video_path)
        print(f'{video_path} -> {new_video_path}')