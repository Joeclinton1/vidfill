import math
from joblib import load


class PolygonMatcher:
    def __init__(self, max_dist):
        self.knn = load("./machine learning models/contour_matcher_knn.joblib")
        self.max_dist = max_dist

    def normalise(self, shape_sim, ratio_area, dist):
        shape_sim = math.tanh(shape_sim)
        ratio_area = math.tanh(1 / ratio_area - 1) if ratio_area < 1 else math.tanh(ratio_area - 1)
        dist = dist/(self.max_dist / 2)
        return shape_sim, ratio_area, dist

    def predict_closest_match(self, input_xs):
        input_xs = map(self.normalise, input_xs)
        probs = self.knn.predict_proba(input_xs)[:, 1].tolist()
        prob = max(probs)
        index = probs.index(prob)
        return index, prob