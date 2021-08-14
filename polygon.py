import cv2
import numpy as np
import math


def center(cnt):
    M = cv2.moments(cnt)
    x = int(M["m10"] / M["m00"])
    y = int(M["m01"] / M["m00"])
    return x, y


class Polygon:
    def __init__(self, cnt, fill):
        self.cnt = cnt
        self.fill = fill
        self.area = cv2.contourArea(cnt)
        self.center = center(cnt)

    def find_visual_center(self):
        M = cv2.moments(self.cnt)
        pt = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        dists = np.sum((self.cnt - pt) ** 2, axis=1)
        n = np.argmin(dists)
        pt2 = self.cnt[n]
        # rotate contour list so that the start point is first in the list
        rCnt = np.roll(self.cnt, -1 * n, axis=0)

        dist = 0
        isCloser = False
        for i, cntPt in enumerate(rCnt):
            newDist = np.linalg.norm(cntPt - pt2)
            if isCloser:
                if newDist > dist:
                    pt3 = (rCnt[i - 1] + cntPt) / 2
                    vCenter = (pt2 + pt3) / 2
                    vCt_t = (vCenter[0], vCenter[1])
                    if cv2.pointPolygonTest(self.cnt, vCt_t, measureDist=False) == 1:
                        return vCt_t
                    else:
                        isCloser = False
            else:
                if newDist < dist:
                    isCloser = True
            dist = newDist
        return False

    def find_closest_match(self, polygons, polygon_matcher):
        polygon_variables = []
        for polygon_id, polygon in polygons.items():
            polygon_variables.append({
                "id":polygon_id,
                "value": (
                    self.shape_sim(polygon),
                    self.ratio_area(polygon),
                    self.distance(polygon)
                )
            })

        input_x_values = [x["value"] for x in polygon_variables]
        index, prob = polygon_matcher.predict_closest_match(input_x_values)
        closest_match_id = polygon_variables[index]["id"]
        return prob, closest_match_id

    def is_point_inside(self, point):
        return cv2.pointPolygonTest(self.cnt, point, measureDist=False) == 1

    def dist_to_nearest_edge(self, point):
        cv2.pointPolygonTest(self.cnt, point, measureDist=True)

    def shape_sim(self, polygon):
        return cv2.matchShapes(self.cnt, polygon.cnt, 1, 0.0)

    def ratio_area(self, polygon):
        return polygon.area / self.area

    def distance(self, polygon):
        x1, y1 = self.center
        x2, y2 = polygon.center
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)