import glob
import os

def str2list(str):
    return [None if x == "None" else int(x) for x in str.split()]


def str2tupleList(str):
    tuple_list = []
    for x in str.split():
        val = None if x == "None" else (int(y) for y in x.split(","))
        tuple_list.append(val)
    return tuple_list


def stringify(obj):
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, list):
        if isinstance(obj[0], tuple):
            return " ".join([
                ",".join([str(y) for y in x]) for x in obj
            ])
        else:
            return " ".join([str(x) for x in obj])

    if isinstance(obj, int):
        return obj


def get_min_max_frame(folder_path):
    svg_frames = glob.glob("%s/frame*.svg" % folder_path)
    if svg_frames:
        min_frame = int(min(svg_frames).split("\\")[-1][5:-4])
        max_frame = max([int(a.split("\\")[-1][5:-4]) for a in svg_frames])
        return  min_frame, max_frame
    raise FileNotFoundError