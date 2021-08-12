from lxml import etree as ET
import cv2
import numpy as np
import re
import math
from joblib import dump, load
import copy

class ContoursHandler:
    def __init__(self, folder_path, vid_w = 0, vid_h=0):
        self.contours = {}  # contours dict of cnt objects contours[i] -> {points: <list>, fill:<str>}
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
        tempContours = []
        closest = (10000,)
        for id, cnt in self.contours.items():
            if cv2.pointPolygonTest(cnt["points"], point, measureDist=False) > 0:
                tempContours.append((id, cnt["points"]))

        for id, points in tempContours:
            dist = cv2.pointPolygonTest(points, point, measureDist=True)
            if dist < closest[0]:
                closest = (dist, id)
        return closest[1]

    def write_new(self, isMult, filepath, newContours):
        root = ET.Element("svg", width=str(self.vid_w), height=str(self.vid_h), xmlns="http://www.w3.org/2000/svg",
                          stroke="black")
        if isMult:
            path = "M3 3,  3 717,1277  717,1277    3,4 3"
            ET.SubElement(root, "path", style="fill:#ffffff", d=path)
        for i, cnt in enumerate(newContours):
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
        for cnt in self.contours.values():
            path = "M" + re.sub('[\[\]]', '', ','.join(map(str, cnt["points"])))
            ET.SubElement(root, "path", style="fill:" + cnt["fill"], d=path)
        tree = ET.ElementTree(root)
        tree.write(filepath)

    def read(self, frame):
        self.contours = {}
        self.tk_polygons = []
        tree = ET.parse(self.folder_path + "/frame%d.svg" % frame)
        for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
            path_points = path.get("d")[1:].split(",")
            fill = path.get("style")[6:]
            id = int(path.get("id"))
            for i, s in enumerate(path_points):
                path_points[i] = list(map(int, s.split()))

            self.tk_polygons.append((id, [item for sublist in path_points for item in sublist], fill))
            self.contours[id] = {
                "points": np.array(path_points),
                "fill": "#" + fill
            }
        return self.contours #Returns dictionary of all the contour objects

    def clear_contours_in_range(self, s_frame, e_frame):
        for i in range(s_frame, e_frame + 1):
            filepath = self.folder_path + "/frame%d.svg" % i
            tree = ET.parse(filepath)
            for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
                path.attrib["style"] = "fill:#ffffff"
            tree.write(filepath)

    def match_all(self, contour_objs, contour_objs2): # Expects two dicts of {id-> contour object}
        contour_objs2_copy = copy.deepcopy(contour_objs2)
        matches = {}
        for cnt_id, cnt_obj in contour_objs.items():
            prob, match_id = self.find_closest_match_knn(cnt_obj, contour_objs2_copy)
            if prob > 0.5:
                matches[cnt_id] = match_id
                del contour_objs2_copy[match_id]
            else:
                matches[cnt_id] = None
        unmatched = contour_objs2_copy
        return matches, unmatched

    def find_closest_match_knn(self, src_cnt_obj, target_contour_objs):
        src_cnt = src_cnt_obj["points"]
        cnt_area = cv2.contourArea(src_cnt )
        cnt_center = self.center(src_cnt )

        input_xs = []
        for target_cnt_id, target_cnt_obj in target_contour_objs.items():
            target_cnt = target_cnt_obj["points"]
            shape_sim = math.tanh(cv2.matchShapes(src_cnt , target_cnt, 1, 0.0))
            ratio_area = cv2.contourArea(target_cnt) / cnt_area
            ratio_area = math.tanh(1 / ratio_area - 1) if ratio_area < 1 else math.tanh(ratio_area - 1)
            dist = self.dist_between_points(cnt_center, self.center(target_cnt)) / (self.max_dist / 2)
            input_xs.append({
                "id":target_cnt_id,
                "value":(shape_sim, ratio_area,dist)
            })

        input_x_values = [x["value"] for x in input_xs]
        probs = self.knn.predict_proba(input_x_values)[:, 1].tolist()
        prob = max(probs)
        closest_match_id = input_xs[probs.index(prob)]["id"]
        return prob, closest_match_id

    def find_closest_match(self, cnt, contours):

        def probability_match(shape_sim, ratio_area, dist):
            closeness = shape_sim / 3 + ratio_area / 1.7 + dist / 90
            if closeness < 20:
                prob = 2 / (1 + math.exp(closeness))  # converts to value between 0 and 1
                """
                print("shape_sim: ",shape_sim / 3, " ratio_area: ",ratio_area / 1.7 , " dist: ",dist / 90)
                print("closeness: ", closeness)
                print("prob: ", prob)
                """
            else:
                prob = 0
            return prob

        cnt_area = cv2.contourArea(cnt)
        cnt_center = self.center(cnt)

        best = (0, None, None)
        for cnt2_index, (cnt2_id, cnt2, _) in enumerate(contours):
            ratio_area = abs(cv2.contourArea(cnt2) / cnt_area - 1)
            dist = self.dist_between_points(cnt_center, self.center(cnt))
            shape_sim = cv2.matchShapes(cnt, cnt2, 1, 0.0)

            prob = probability_match(shape_sim, ratio_area, dist)
            if prob >= best[0]:
                best = (prob, cnt2_id, cnt2_index)
        return best

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