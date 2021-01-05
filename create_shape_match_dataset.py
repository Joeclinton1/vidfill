from contours import Contours
import cv2
from lxml import etree as ET
import numpy as np
import glob
import math
import pandas as pd
import random


class MatchDataset:
    def __init__(self, folder_path, vid_filepath):
        self.vid_filepath = vid_filepath

        # Get the video and video properties
        vid_cap = cv2.VideoCapture(self.vid_filepath)
        self.vid_width = vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.vid_height = vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.vid_frame_count = int(vid_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.folder_path = folder_path

        # Get min max frame
        svg_frames = glob.glob("%s/frame*.svg" % self.folder_path)
        if svg_frames:
            self.min_frame = int(min(svg_frames).split("\\")[-1][5:-4])
            self.max_frame = max([int(a.split("\\")[-1][5:-4]) for a in svg_frames])
            self.frame = self.min_frame

        self.max_area = self.vid_height*self.vid_width
        self.max_dist = math.sqrt(self.vid_height ** 2 + self.vid_width ** 2)

    def contours_read(self, frame):
        self.contours = []
        tree = ET.parse(self.folder_path + "/frame%d.svg" % frame)
        for path in tree.iterfind("//{http://www.w3.org/2000/svg}path"):
            path_points = path.get("d")[1:].split(",")
            for i, s in enumerate(path_points):
                path_points[i] = list(map(int, s.split()))

            self.contours.append(np.array(path_points))
        return self.contours

    def cpoints_read(self):
        def str2list(str):
            return [int(x) for x in str.split()]

        cpoints = []
        tree = ET.parse(self.folder_path + "/colour_points.xml")
        for c_point in tree.iterfind("//cPoint"):
            types = str2list(c_point.get("types"))
            type = types[0]
            motion = types[1]
            if type == 3 and motion == 3: # Only use cpoints of type = multiple and motion == 2
                points = []
                for point in c_point:
                    points.append(str2list(point.text))
                frames = str2list(c_point.get("frames"))
                cpoints.append({"points":points, "frames":frames})
        return cpoints

    def build_dataset(self):
        cpoints = self.cpoints_read()
        dataset = self.dataset_from_cpoints(cpoints)
        return dataset

    def dataset_from_cpoints(self, cpoints):
        X = []
        y = []
        contour_chains = {}
        for frame in range(self.min_frame, self.max_frame + 1):
            print("frame: %s/%s"%(frame, self.max_frame))
            self.contours_read(frame)
            for i, cpoint in enumerate(cpoints):
                if frame in cpoint["frames"]:
                    point = cpoint["points"][cpoint["frames"].index(frame)]
                    cnt_index, cnt = self.find_closest(tuple(point))
                    if i in contour_chains:
                        prev_cnt = contour_chains[i][-1]
                        attributes = self.get_attributes(prev_cnt, self.contours, cnt_index)
                        X.extend(attributes)
                        y.extend([True]+[False]*(len(attributes)-1))
                        contour_chains[i].append(cnt)
                    else:
                        contour_chains[i] = [cnt]

        return X, y

    def find_closest(self, point: tuple, include_edges = False):
        tempContours = []
        closest = (math.inf,)
        for i, cnt in enumerate(self.contours):
            thresh = -1 if include_edges else 0
            if cv2.pointPolygonTest(cnt, point, measureDist=False) > thresh:
                tempContours.append((i, cnt))

        for i, cnt in tempContours:
            dist = cv2.pointPolygonTest(cnt, point, measureDist=True)
            if dist <= closest[0]:
                closest = (dist, (i, cnt))
        if not (tempContours and include_edges):
            return self.find_closest(point, include_edges = True)
        else:
            return closest[1]

    def get_attributes(self, cnt, contours, true_index):
        attributes_true = []
        attributes_false = []

        def center(cnt):
            M = cv2.moments(cnt)
            x = int(M["m10"] / M["m00"])
            y = int(M["m01"] / M["m00"])
            return x, y

        def dist_between_points(C1, C2):
            x1, y1 = C1
            x2, y2 = C2
            return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

        cnt_area = cv2.contourArea(cnt)
        cnt_center = center(cnt)

        for i, cnt2 in enumerate(contours):
            shape_sim = math.tanh(cv2.matchShapes(cnt, cnt2, 1, 0.0))
            ratio_area = cv2.contourArea(cnt2) / cnt_area
            ratio_area = math.tanh(1/ratio_area-1) if ratio_area<1 else math.tanh(ratio_area-1)
            dist = dist_between_points(cnt_center, center(cnt2))/self.max_dist
            attr = [round(x,6) for x in [shape_sim, ratio_area, dist]]
            if i == true_index:
                attributes_true.append(attr)
            else:
                attributes_false.append(attr)
        random.shuffle(attributes_false)
        return attributes_true + attributes_false[:2]


if __name__ == "__main__":
    match_dataset = MatchDataset(r"C:\Users\Joe\OneDrive\Documents\youtube\Asdf11\frames\frames_01",
                                 r"C:\Users\Joe\OneDrive\Documents\youtube\Asdf11\asdfmovie11-15fps.mp4")

    X, y = match_dataset.build_dataset()
    data = {
        "Label": [int(x) for x in y],
        "Is match?": [str(x) for x in y],
        "Shape similarity": [x[0] for x in X],
        "Ratio area": [x[1] for x in X],
        "Distance": [x[2] for x in X],
    }
    df = pd.DataFrame(data)
    df.to_csv("./data/shape_match_data.csv")