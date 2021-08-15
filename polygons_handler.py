from lxml import etree as ET
import cv2
import numpy as np
import re
import math
import copy
from ML.contour_matching.polygon_matcher import PolygonMatcher
from polygon import Polygon


class PolygonsHandler:
    def __init__(self, folder_path, vid_w=0, vid_h=0):
        self.polygons = {}  # polygons dict of polygons: polygons[i] -> {points: <list>, fill:<str>}
        self.tk_polygons = []
        self.vid_w = vid_w
        self.vid_h = vid_h
        self.folder_path = folder_path
        self.max_dist = math.sqrt(self.vid_h ** 2 + self.vid_w ** 2)
        self.polygon_matcher = PolygonMatcher(self.max_dist)

    def write_new(self, is_mult, frame, polygons=None):
        if polygons:
            self.polygons = polygons

        root = ET.Element("svg", width=str(self.vid_w), height=str(self.vid_h), xmlns="http://www.w3.org/2000/svg",
                          stroke="black")
        if is_mult:
            path = "M3 3,  3 717,1277  717,1277    3,4 3"
            ET.SubElement(root, "path", style="fill:#ffffff", d=path)
        for id, polygon in self.polygons.items():
            # epsilon = 0.02*cv2.arcLength(cnt,True)
            cnt = polygon.cnt
            approx = cv2.approxPolyDP(cnt, 0.6, False)
            cnt_as_list = np.vstack(approx).squeeze()
            if len(approx) < 4 or (cv2.contourArea(approx) > self.vid_w * self.vid_h * 0.9 and is_mult):
                continue
            else:
                path = "M" + re.sub('[\[\]]', '', ','.join(map(str, cnt_as_list)))
                ET.SubElement(root, "path", id=str(id), style="fill:" + polygon.fill, d=path)
        tree = ET.ElementTree(root)
        tree.write(self.folder_path + "/frame%d.svg" % frame)

    def write(self, frame, polygons=None):
        if polygons:
            self.polygons = polygons

        root = ET.Element("svg", width=str(self.vid_w), height=str(self.vid_h), xmlns="http://www.w3.org/2000/svg",
                          stroke="black")
        for polygon in self.polygons.values():
            path = "M" + re.sub('[\[\]]', '', ','.join(map(str, polygon.cnt)))
            ET.SubElement(root, "path", style="fill:" + polygon.fill, d=path)
        tree = ET.ElementTree(root)
        tree.write(self.folder_path + "/frame%d.svg" % frame)

    def read(self, frame):
        self.polygons = {}
        self.tk_polygons = []
        tree = ET.parse(self.folder_path + "/frame%d.svg" % frame)
        for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
            path_points = path.get("d")[1:].split(",")
            fill = path.get("style")[6:]
            id = int(path.get("id"))
            for i, s in enumerate(path_points):
                path_points[i] = list(map(int, s.split()))

            self.tk_polygons.append((id, [item for sublist in path_points for item in sublist], fill))
            self.polygons[id] = Polygon(
                cnt=np.array(path_points),
                fill= "#" + fill
            )
        return self.polygons  # Returns dictionary of all the contour objects

    def set_polygons_white_in_range(self, s_frame, e_frame):
        for i in range(s_frame, e_frame + 1):
            filepath = self.folder_path + "/frame%d.svg" % i
            tree = ET.parse(filepath)
            for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
                path.attrib["style"] = "fill:#ffffff"
            tree.write(filepath)

    @staticmethod
    def match_all(polygons_prev, polygons_new):  # Expects two dicts of {id-> contour object}
        polygons_new_copy = copy.deepcopy(polygons_new)
        matches = {}
        for poly_id, polygon in polygons_prev.items():
            prob, match_id = polygon.find_closest_match(polygons_new_copy)
            if prob > 0.5:
                matches[poly_id] = match_id
                del polygons_new_copy[match_id]
            else:
                matches[poly_id] = None
        unmatched = polygons_new_copy
        return matches, unmatched

    def closest_polygon_to_point(self, point):
        closest = (None, math.inf)
        for id, polygon in self.polygons.items():
            if polygon.is_point_inside(point):
                dist = polygon.dist_to_nearest_edge(point)
                if dist < closest[1]:
                    closest = (id, dist)
        return closest[0]
