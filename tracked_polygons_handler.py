from lxml import etree as ET
import math
from polygons_handler import PolygonsHandler
import glob
from util import get_min_max_frame
import json

"""
self.tracked_polygons structure is:

{tracked_poly id: {
    "range": [min, max],
    "indices": [index_1, index 2, ...]
]}
"""


def replace_path_points_data(folder_path):
    polygons_handler = PolygonsHandler(folder_path)
    tracked_polygons_handler = TrackedPolygonsHandler(folder_path)
    num_frames = len(glob.glob("%s/frame*.svg" % folder_path))
    tracked_polygons = tracked_polygons_handler.tracked_polygons
    for keyframe in tracked_polygons:
        keyframe.path_points = []

    for frame in range(1, num_frames + 1):
        polygons_handler.read(frame)
        id_to_tracked_polyid_dict = tracked_polygons_handler.get_id_to_tracked_polyid_dict(frame)
        for id, polygon in polygons_handler.polygons.items():
            cnt = polygon.cnt
            tracked_poly_id = id_to_tracked_polyid_dict[id]
            keyframe = tracked_polygons[tracked_poly_id]
            start_frame = keyframe.range[0]
            keyframe.path_points[frame - start_frame] = cnt.center

    tracked_polygons_handler.write()


class TrackedPolygon(object):
    def __init__(self, range=None, indices=None, path_points=None):
        self.range = range
        self.indices = indices
        self.path_points = path_points if path_points else [None] * len(indices)


class TrackedPolygonData(object):
    def __init__(self, tracked_poly_id=None, frame=None, start=None, end=None, path_points=None):
        self.tracked_poly_id = tracked_poly_id
        self.temporal_label = "start" if frame == start else "middle" if start < frame < end else "end"
        self.path_points = path_points


class TrackedPolygonsHandler:
    def __init__(self, folder):
        self.folder = folder
        self.tracked_polygons = {}

        try:
            self.read()
            if self.tracked_polygons == {}:
                self.create_tracked_polygons_file()
        except OSError:
            self.create_tracked_polygons_file()

    def create_tracked_polygons_file(self):
        min_frame = get_min_max_frame(self.folder)[0]
        # generate dict of tracked_polygons objects for first frame
        tracked_polygons = {}
        polygons_handler = PolygonsHandler(self.folder)
        polygons = polygons_handler.read(1)
        for polygon_id, polygon in polygons.items():
            tracked_polygons[polygon_id] = TrackedPolygon(
                range=[min_frame, min_frame],
                indices=[polygon_id],
                path_points=[polygon.center]
            )
        self.tracked_polygons = tracked_polygons
        self.write()

    def write(self):
        root = ET.Element("tracked_polygons")
        for tracked_poly_id, keyframe in self.tracked_polygons.items():
            stringified_keyframe_attributes = {key: json.dumps(val) for key, val in keyframe.__dict__.items()}
            ET.SubElement(
                root,
                "tracked_poly",
                tracked_poly_id=str(tracked_poly_id),
                **stringified_keyframe_attributes
            )

        tree = ET.ElementTree(root)
        tree.write(self.folder + "/tracked_polygons.xml")

    def read(self):
        self.tracked_polygons = {}
        tree = ET.parse(self.folder + "/tracked_polygons.xml")
        for tracked_poly in tree.iterfind("//tracked_poly"):
            tracked_poly_id = int(tracked_poly.get('tracked_poly_id'))
            keyframe_attributes = {key: json.loads(val) for key, val in tracked_poly.items() if
                                   key != 'tracked_poly_id'}
            keyframe = TrackedPolygon(**keyframe_attributes)

            self.tracked_polygons[tracked_poly_id] = keyframe

    def clear_tracked_polygons_in_range(self, s_frame, e_frame):
        self.tracked_polygons = list(
            filter(lambda x: not s_frame <= x[-1][0] <= e_frame,
                   self.tracked_polygons))  # removes tracked_polys inside of frame range
        self.write()

    def get_id_to_tracked_polyid_dict(self, frame):  # cnt -> tracked_poly_id
        d = {}
        for tracked_poly_id, keyframe in self.tracked_polygons.items():
            range = keyframe.range
            f_min = range[0]
            f_max = math.inf if len(keyframe.range) == 1 else keyframe.range[1]

            if f_min <= frame <= f_max:
                # print(props["indices"], f_min, f_max, frame)
                id = keyframe.indices[frame - f_min]
                d[id] = tracked_poly_id
        return d

    def get_tracked_poly_data_dict(self, frame):

        """
        cnt_time_pos_dict tells you for a given frame,
         - which tracked_polys match which keyframe paths
         - and what time position they have
        """

        id_to_tracked_polyid_dict = self.get_id_to_tracked_polyid_dict(frame)
        d = {}
        for id, tracked_poly_id in id_to_tracked_polyid_dict.items():
            keyframe = self.tracked_polygons[tracked_poly_id]
            f_min = keyframe.range[0]
            f_max = math.inf if len(keyframe.range) == 1 else keyframe.range[1]
            d[id] = TrackedPolygonData(
                tracked_poly_id=tracked_poly_id,
                frame=frame,
                start=f_min,
                end=f_max,
                path_points=keyframe.path_points
            )
        return d

    def generate_tracked_polygons(self, min_frame, max_frame, polygons_handler):
        # read contours for first frame
        polygons_prev = polygons_handler.read(min_frame)

        # Remove indexes from tracked_polygons after min_frame
        for tracked_poly_id, tracked_poly_obj in self.tracked_polygons.items():
            min_range, max_range = tracked_poly_obj.range
            if min_range > min_frame and max_range < max_frame:
                self.tracked_polygons[tracked_poly_id].indices = tracked_poly_obj.indices[:min_frame - min_range + 1]

        # iterate through the frames,  matching polygons with those from the frame before and extending the tracked_polygons
        for frame in range(min_frame + 1, max_frame + 1):
            print("Generating tracked_polygons for frame: ", frame)
            polygons = polygons_handler.read(frame)

            # foreach contour we try to pair it with the matching contour_prev, otherwise we pair it with None
            # unmatched_dict contains the polygons in current frame not matched with one from polygons_prev
            match_dict, unmatched_dict = polygons_handler.match_all(polygons_prev, polygons)

            # for each matching pair, we find which tracked_poly to extend,
            # by getting the tracked_poly id of the src contour
            id_to_tracked_polyid_dict = self.get_id_to_tracked_polyid_dict(frame - 1)
            for cnt1_id, cnt2_id in match_dict.items():
                if cnt1_id not in id_to_tracked_polyid_dict:
                    return
                if id_to_tracked_polyid_dict[cnt1_id] not in self.tracked_polygons:
                    return
                tracked_poly = self.tracked_polygons[id_to_tracked_polyid_dict[cnt1_id]]
                if cnt2_id is None:
                    tracked_poly.range[1] = frame - 1
                else:
                    tracked_poly.indices.append(cnt2_id)
                    tracked_poly.range[1] = frame

            # for each unmatched pair create a new tracked_poly object and append to the tracked_polygons dict
            for cnt2_id, cnt2_obj in unmatched_dict.items():
                self.tracked_polygons[len(self.tracked_polygons) + 1] = TrackedPolygon(
                    range=[frame, frame],
                    indices=[cnt2_id],
                    path_points=[polygons_handler.center(cnt2_obj["points"])]
                )

            polygons_prev = polygons.copy()


if __name__ == "__main__":
    fp = r"C:\github_personal\vidfill 2\data\asdf12\frames\frames_01"
    replace_path_points_data(fp)
