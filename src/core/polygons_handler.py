from lxml import etree as ET
import cv2
import numpy as np
import re
import math
import copy
from src.core.polygon import Polygon
from src.ml.contour_matching.polygon_matcher import PolygonMatcher


class PolygonsHandler:
    def __init__(self, driver):
        self.driver = driver
        self.polygons = {}  # polygons dict of polygons: polygons[i] -> {points: <list>, fill:<str>}

    def write_new(self, is_mult, frame):
        width, height = self.driver.vid_width, self.driver.vid_height

        root = ET.Element("svg", width=str(width), height=str(height), xmlns="http://www.w3.org/2000/svg",
                          stroke="black")
        if is_mult:
            path = "M3 3,  3 717,1277  717,1277    3,4 3"
            ET.SubElement(root, "path", style="fill:#ffffff", d=path)
        for id, polygon in self.polygons.items():
            # epsilon = 0.02*cv2.arcLength(cnt,True)
            cnt = polygon.cnt
            approx = cv2.approxPolyDP(cnt, 0.6, False)
            cnt_as_list = np.vstack(approx).squeeze()
            if len(approx) < 4 or (cv2.contourArea(approx) > width* height * 0.9 and is_mult):
                continue
            else:
                path = "M" + re.sub('[\[\]]', '', ','.join(map(str, cnt_as_list)))
                ET.SubElement(root, "path", id=str(id), style="fill:" + polygon.fill, d=path)
        tree = ET.ElementTree(root)
        tree.write(self.driver.folder_path + "/frame%d.svg" % frame)

    def write(self, frame):
        width, height = self.driver.vid_width, self.driver.vid_height
        root = ET.Element("svg", width=str(width), height=str(height), xmlns="http://www.w3.org/2000/svg",
                          stroke="black")
        for polygon in self.polygons.values():
            path = "M" + re.sub('[\[\]]', '', ','.join(map(str, polygon.cnt)))
            ET.SubElement(root, "path", style="fill:" + polygon.fill, d=path)
        tree = ET.ElementTree(root)
        tree.write(self.driver.folder_path + "/frame%d.svg" % frame)

    def read(self, frame):
        self.polygons = {}
        tree = ET.parse(self.driver.folder_path + "/frame%d.svg" % frame)
        for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
            path_points = path.get("d")[1:].split(",")
            fill = path.get("style")[6:]
            id = int(path.get("id"))
            for i, s in enumerate(path_points):
                path_points[i] = list(map(int, s.split()))

            self.polygons[id] = Polygon(
                cnt=np.array(path_points),
                fill= "#" + fill
            )
        return self.polygons  # Returns dictionary of all the contour objects

    def set_polygons_white_in_range(self, s_frame, e_frame):
        for i in range(s_frame, e_frame + 1):
            filepath = self.driver.folder_path + "/frame%d.svg" % i
            tree = ET.parse(filepath)
            for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
                path.attrib["style"] = "fill:#ffffff"
            tree.write(filepath)

    def match_all(self, polygons_prev, polygons_new):  # Expects two dicts of {id-> contour object}
        polygons_new_copy = copy.deepcopy(polygons_new)
        matches = {} # polygon id 1 -> matched polygon id 2
        for poly_id, polygon in polygons_prev.items():
            prob, match_id = self.find_closest_match(polygon, polygons_new_copy)
            if prob > 0.5:
                matches[poly_id] = match_id
                del polygons_new_copy[match_id]
            else:
                matches[poly_id] = None
        unmatched_polygons = polygons_new_copy

        # matched gives pairs of polygons which were matched
        # unmatched_polygons gives the polygons in current frame not matched with one from polygons_prev

        # matches: {polygon1 id => polygon 2 id}
        # unmatched_polygons: {polygon id => polygon}

        return matches, unmatched_polygons

    def find_closest_match(self, polygon1, polygons):
        max_dist = math.sqrt(self.driver.vid_height ** 2 + self.driver.vid_width ** 2)
        polygon_matcher = PolygonMatcher(max_dist)
        polygon_variables = []
        for polygon_id, polygon2 in polygons.items():
            polygon_variables.append({
                "id":polygon_id,
                "value": (
                    polygon1.shape_sim(polygon2),
                    polygon1.ratio_area(polygon2),
                    polygon1.distance(polygon2)
                )
            })

        input_x_values = [x["value"] for x in polygon_variables]
        index, prob = polygon_matcher.predict_closest_match(input_x_values)
        closest_match_id = polygon_variables[index]["id"]
        return prob, closest_match_id

    def closest_polygon_to_point(self, point):
        closest = (None, math.inf)
        for id, polygon in self.polygons.items():
            if polygon.is_point_inside(point):
                dist = polygon.dist_to_nearest_edge(point)
                if dist < closest[1]:
                    closest = (id, dist)
        return closest[0]
