from lxml import etree as ET
import cv2
import numpy as np
import re
import math
from joblib import dump, load

class Contours:
    def __init__(self, folder_path, vidW, vidH):
        self.contours = []  # contours array of tuples contours[i] -> (cnt, fill)
        self.tk_polygons = []
        self.vidW = vidW
        self.vidH = vidH
        self.folder_path = folder_path
        self.knn = load("./machine learning models/contour_matcher_knn.joblib")
        self.max_dist = math.sqrt(self.vidH ** 2 + self.vidW ** 2)

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
        for i, c in enumerate(self.contours):
            if cv2.pointPolygonTest(c[0], point, measureDist=False) > 0:
                tempContours.append((c, i))

        for c in tempContours:
            dist = cv2.pointPolygonTest(c[0][0], point, measureDist=True)
            if dist < closest[0]:
                closest = (dist, c[1])
        return closest[1]

    def write_new(self, isMult, filepath, newContours):
        root = ET.Element("svg", width=str(self.vidW), height=str(self.vidH), xmlns="http://www.w3.org/2000/svg",
                          stroke="black")
        if isMult:
            path = "M3 3,  3 717,1277  717,1277    3,4 3"
            ET.SubElement(root, "path", style="fill:#ffffff", d=path)
        for i, cnt in enumerate(newContours):
            # epsilon = 0.02*cv2.arcLength(cnt,True)
            approx = cv2.approxPolyDP(cnt, 0.6, False)
            listCnt = np.vstack(approx).squeeze()
            if len(approx) < 4 or (cv2.contourArea(approx) > self.vidW * self.vidH * 0.9 and isMult):
                continue
            else:
                path = "M" + re.sub('[\[\]]', '', ','.join(map(str, listCnt)))
                ET.SubElement(root, "path", id=str(i), style="fill:#ffffff", d=path)
        tree = ET.ElementTree(root)
        tree.write(filepath)

    def modify(self, filepath):
        root = ET.Element("svg", width=str(self.vidW), height=str(self.vidH), xmlns="http://www.w3.org/2000/svg",
                          stroke="black")
        for cnt in self.contours:
            path = "M" + re.sub('[\[\]]', '', ','.join(map(str, cnt[0])))
            ET.SubElement(root, "path", style="fill:" + cnt[1], d=path)
        tree = ET.ElementTree(root)
        tree.write(filepath)

    def read(self, frame):
        self.contours = []
        tree = ET.parse(self.folder_path + "/frame%d.svg" % frame)
        for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
            path_points = path.get("d")[1:].split(",")
            fill = path.get("style")[6:]
            id = int(path.get("id"))
            for i, s in enumerate(path_points):
                path_points[i] = list(map(int, s.split()))

            self.tk_polygons.append((id, [item for sublist in path_points for item in sublist], fill))
            self.contours.append([id, np.array(path_points), "#" + fill])
        return self.contours

    def clear_contours_in_range(self, s_frame, e_frame):
        for i in range(s_frame, e_frame + 1):
            filepath = self.folder_path + "/frame%d.svg" % i
            tree = ET.parse(filepath)
            for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
                path.attrib["style"] = "fill:#ffffff"
            tree.write(filepath)

    def track_contours(self, min_frame, max_frame):
        def get_shapeid_dict(keyframes): # cnt -> shape_id
            d = {}
            for shape_id, props in keyframes.items():
                if props["range"][1] is None:
                    id = props["indexes"][-1]
                    d[id] = shape_id
            return d

        contours1 = self.read(min_frame)
        key_frames = {}  # shape id -> (min, max) , [cnt1_id, cnt2_id, ...]

        # setup keyframes for first frame
        for cnt_id, *_ in contours1:
            key_frames[cnt_id] = {"range": [min_frame, None], "indexes": [cnt_id]}

        # iterate through the frames,  matching contours with those from the frame before and extending the keyframes
        for frame in range(min_frame + 1, max_frame+1):
            print("Generating keyframes for frame: ", frame)
            contours2 = self.read(frame)
            # foreach contour2 we try to pair it with the matching contour 1, otherwise we pair it with None
            matches, unmatched_contour2s = self.match_all(contours1, contours2)

            id_to_shapeid = get_shapeid_dict(key_frames)
            for cnt1_id, cnt2_id in matches.items():
                shape_id = id_to_shapeid[cnt1_id]
                if cnt2_id is None:
                    key_frames[shape_id]["range"][1] = frame - 1
                else:
                    key_frames[shape_id]["indexes"].append(cnt2_id)
                    if frame == max_frame:
                        key_frames[shape_id]["range"][1] = frame
            for cnt2_id in unmatched_contour2s:
                key_frames[len(key_frames) + 1] = {"range": [frame, None], "indexes": [cnt2_id]}

            contours1 = contours2.copy()
        return key_frames

    def match_all(self, contours1, contours2):
        contours2 = contours2.copy()
        matches = {}
        for cnt_id, cnt, _ in contours1:
            prob, match_id, match_index = self.find_closest_match_knn(cnt, contours2)
            if prob > 0.5:
                matches[cnt_id] = match_id
                del contours2[match_index]
            else:
                matches[cnt_id] = None
        unmatched = [a[0] for a in contours2]
        return matches, unmatched

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

    def find_closest_match_knn(self, cnt, contours):
        cnt_area = cv2.contourArea(cnt)
        cnt_center = self.center(cnt)

        X = []
        for _, cnt2, _ in contours:
            shape_sim = math.tanh(cv2.matchShapes(cnt, cnt2, 1, 0.0))
            ratio_area = cv2.contourArea(cnt2) / cnt_area
            ratio_area = math.tanh(1 / ratio_area - 1) if ratio_area < 1 else math.tanh(ratio_area - 1)
            dist = self.dist_between_points(cnt_center, self.center(cnt2)) / (self.max_dist / 2)
            X.append([shape_sim, ratio_area,dist])

        probs = self.knn.predict_proba(X)[:, 1]
        prob = max(probs)
        cnt2_index = np.argmax(probs)
        cnt2_id = contours[cnt2_index][0]
        return prob, cnt2_id, cnt2_index

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