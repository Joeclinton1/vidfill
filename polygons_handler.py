from lxml import etree as ET
import cv2
import numpy as np
import re
import math
from joblib import dump, load
import copy


class PolygonsHandler:
    def __init__(self, folder_path, vid_w = 0, vid_h=0):
        self.polygons = {}  # polygons dict of cnt objects polygons[i] -> {points: <list>, fill:<str>}
        self.tk_polygons = []
        self.vid_w = vid_w
        self.vid_h = vid_h
        self.folder_path = folder_path
        self.knn = load("./machine learning models/contour_matcher_knn.joblib")
        self.max_dist = math.sqrt(self.vid_h ** 2 + self.vid_w ** 2)

    def find_visual_center(self, cnt):
        M = cv2.moments(cnt)
        pt = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        dists = np.sum((cnt - pt) ** 2, axis=1)
        n = np.argmin(dists)
        pt2 = cnt[n]
        # rotate contour list so that the start point is first in the list
        rCnt = np.roll(cnt, -1 * n, axis=0)

        dist = 0
        isCloser = False
        for i, cntPt in enumerate(rCnt):
            newDist = np.linalg.norm(cntPt - pt2)
            if isCloser:
                if newDist > dist:
                    pt3 = (rCnt[i - 1] + cntPt) / 2
                    vCenter = (pt2 + pt3) / 2
                    vCt_t = (vCenter[0], vCenter[1])
                    if cv2.pointPolygonTest(cnt, vCt_t, measureDist=False) == 1:
                        return vCt_t
                    else:
                        isCloser = False
            else:
                if newDist < dist:
                    isCloser = True
            dist = newDist
        return False

    def escape_contour(self, pt, cnt, cnt2):
        print(pt)
        dists = np.sum((cnt - pt) ** 2, axis=1)
        n = np.argmin(dists)
        pt2 = cnt[n]

        dists = np.sum((cnt2 - pt2) ** 2, axis=1)
        n = np.argmin(dists)
        pt3 = cnt2[n]

        pt4 = (pt2 + pt3) / 2
        return (pt4[0], pt4[1])

    def find_closest(self, point):
        temp_polygons = []
        closest = (10000,)
        for id, cnt in self.polygons.items():
            if cv2.pointPolygonTest(cnt["points"], point, measureDist=False) > 0:
                temp_polygons.append((id, cnt["points"]))

        for id, points in temp_polygons:
            dist = cv2.pointPolygonTest(points, point, measureDist=True)
            if dist < closest[0]:
                closest = (dist, id)
        return closest[1]

    def write_new_contours(self, isMult, filepath, contours):
        root = ET.Element("svg", width=str(self.vid_w), height=str(self.vid_h), xmlns="http://www.w3.org/2000/svg",
                          stroke="black")
        if isMult:
            path = "M3 3,  3 717,1277  717,1277    3,4 3"
            ET.SubElement(root, "path", style="fill:#ffffff", d=path)
        for i, cnt in enumerate(contours):
            # epsilon = 0.02*cv2.arcLength(cnt,True)
            approx = cv2.approxPolyDP(cnt, 0.6, False)
            listCnt = np.vstack(approx).squeeze()
            if len(approx) < 4 or (cv2.contourArea(approx) > self.vid_w * self.vid_h * 0.9 and isMult):
                continue
            else:
                path = "M" + re.sub('[\[\]]', '', ','.join(map(str, listCnt)))
                ET.SubElement(root, "path", id=str(i), style="fill:#ffffff", d=path)
        tree = ET.ElementTree(root)
        tree.write(filepath)

    def modify(self, filepath):
        root = ET.Element("svg", width=str(self.vid_w), height=str(self.vid_h), xmlns="http://www.w3.org/2000/svg",
                          stroke="black")
        for cnt in self.polygons.values():
            path = "M" + re.sub('[\[\]]', '', ','.join(map(str, cnt["points"])))
            ET.SubElement(root, "path", style="fill:" + cnt["fill"], d=path)
        tree = ET.ElementTree(root)
        tree.write(filepath)

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
            self.polygons[id] = {
                "points": np.array(path_points),
                "fill": "#" + fill
            }
        return self.polygons #Returns dictionary of all the contour objects

    def set_polygons_white_in_range(self, s_frame, e_frame):
        for i in range(s_frame, e_frame + 1):
            filepath = self.folder_path + "/frame%d.svg" % i
            tree = ET.parse(filepath)
            for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
                path.attrib["style"] = "fill:#ffffff"
            tree.write(filepath)

    def match_all(self, polygons_prev, polygons_new): # Expects two dicts of {id-> contour object}
        polygons_new_copy = copy.deepcopy(polygons_new)
        matches = {}
        for poly_id, polygon in polygons_prev.items():
            prob, match_id = self.find_closest_match(polygon, polygons_new_copy)
            if prob > 0.5:
                matches[poly_id] = match_id
                del polygons_new_copy[match_id]
            else:
                matches[poly_id] = None
        unmatched = polygons_new_copy
        return matches, unmatched

    def find_closest_match(self, input_polygons, target_polgon):
        target_cnt = target_polgon["points"]
        cnt_area = cv2.contourArea(target_cnt)
        cnt_center = self.center(target_cnt)

        polygon_variables = []
        for input_poly_id, input_polgon in input_polygons.items():
            input_cnt = input_polgon["points"]
            shape_sim = math.tanh(cv2.matchShapes(target_cnt , input_cnt, 1, 0.0))
            ratio_area = cv2.contourArea(input_cnt) / cnt_area
            ratio_area = math.tanh(1 / ratio_area - 1) if ratio_area < 1 else math.tanh(ratio_area - 1)
            dist = self.dist_between_points(cnt_center, self.center(input_cnt)) / (self.max_dist / 2)
            polygon_variables.append({
                "id":input_poly_id,
                "value":(shape_sim, ratio_area,dist)
            })

        input_x_values = [x["value"] for x in polygon_variables]
        probs = self.knn.predict_proba(input_x_values)[:, 1].tolist()
        prob = max(probs)
        closest_match_id = polygon_variables[probs.index(prob)]["id"]
        return prob, closest_match_id

    @staticmethod
    def center(cnt):
        M = cv2.moments(cnt)
        x = int(M["m10"] / M["m00"])
        y = int(M["m01"] / M["m00"])
        return x, y

    @staticmethod
    def dist_between_points(C1, C2):
        x1, y1 = C1
        x2, y2 = C2
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)