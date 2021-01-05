from lxml import etree as ET
import math
import os

"""
self.key_frames structure is:

{shape id: {
    "range": [min, max],
    "indexes": [index_1, index 2, ...]
]}
"""


class Keyframes:
    def __init__(self, folder):
        self.folder = folder
        self.key_frames = {}

        try:
            self.read()
        except FileNotFoundError:
            self.write()

    def write(self):
        def stringify(dictionary):
            new_dict = {}
            for key, val in dictionary.items():
                if isinstance(val, int):
                    new_dict[key] = str(val)
                elif isinstance(val, list):
                    new_dict[key] = " ".join([str(x) for x in val])
                else:
                    new_dict[key] = val
            return new_dict

        root = ET.Element("Shape-Keyframes")
        for shape_id, props in self.key_frames.items():
            ET.SubElement(root, "shape", shape_id=str(shape_id), **stringify(props))

        tree = ET.ElementTree(root)
        tree.write(self.folder + "/keyframes.xml")

    def read(self):
        def str2list(str):
            return [None if x == "None" else int(x) for x in str.split()]

        self.key_frames = {}
        tree = ET.parse(self.folder + "/keyframes.xml")
        for shape in tree.iterfind("//shape"):
            shape_id = int(shape.get("shape_id"))
            range = str2list(shape.get("range"))
            indexes = str2list(shape.get("indexes"))
            self.key_frames[shape_id] = {
                "range": range,
                "indexes": indexes
            }

    def clear_cpoints_in_range(self, s_frame, e_frame):
        self.key_frames = list(
            filter(lambda x: not s_frame <= x[-1][0] <= e_frame,
                   self.key_frames))  # removes shapes inside of frame range
        self.write()

    def get_id_to_shapeid_dict(self, frame):  # cnt -> shape_id
        d = {}
        for shape_id, props in self.key_frames.items():
            f_min, f_max = props["range"]
            if f_max is None:
                f_max = math.inf
            if f_min <= frame <= f_max:
                #print(props["indexes"], f_min, f_max, frame)
                id = props["indexes"][frame - f_min]
                d[id] = shape_id
        return d

    def get_cnt_time_pos_dict(self, frame):
        id_to_shapeid_dict = self.get_id_to_shapeid_dict(frame)
        d = {}
        for id, shape_id in id_to_shapeid_dict.items():
            start, end = self.key_frames[shape_id]["range"]
            if end is None:
                end = math.inf
            d[id] = ("start" if frame == start else "middle" if start < frame < end else "end"), shape_id
        return d
