import cv2
import numpy as np
from src.core.polygons_handler import PolygonsHandler
from src.core.polygon import Polygon

kernel = np.ones((3, 3), np.uint8)
kernel2 = np.ones((11, 11), np.uint8)
kernel3 = np.ones((1, 1), np.uint8)


class VideoTracer:
    def __init__(self, folder_path, vid_cap, vid_size, num_frames, polygons_handler):
        self.folder_path = folder_path
        self.vid_cap = vid_cap
        self.vid_size = vid_size
        self.num_frames = num_frames
        self.polygons_handler = polygons_handler

    def img2ContoursThresh(self, filepathBMP, threshvalue):
        img = cv2.imread(filepathBMP)
        width, height = self.vid_size
        img = cv2.fastNlMeansDenoising(img, None, 8, 21, 7)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(img, threshvalue, 255, cv2.THRESH_BINARY_INV)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel)
        thresh = cv2.rectangle(thresh, (2, 2), (int(width) - 2, int(height) - 1), 255, 2)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        return contours

    def img2ContoursMult(self, filepathBMP, steps, offsetL, offsetH):
        img = cv2.imread(filepathBMP)
        width, height = self.vid_size
        img = cv2.fastNlMeansDenoising(img, None, 8, 21, 7)
        contours = []
        step = (255 - offsetL - offsetH) / steps
        for i in range(steps):
            offH = offsetL + offsetH if i == steps - 1 else offsetL
            offL = offsetL if i != 0 else 0
            im = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            print(i * step + offL)
            im[(im > (i + 1) * step + offH) | (im < i * step + offL)] = 0
            im[(im >= i * step + offL) & (im <= (i + 1) * step + offH)] = 255
            thresh = cv2.morphologyEx(im, cv2.MORPH_OPEN, kernel)
            thresh = cv2.rectangle(thresh, (1, 1), (int(width) - 1, int(height) - 1), 0, 2)
            subContours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            contours.extend(subContours)
            """im2 = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
            cv2.drawContours(im2, contours, -1, (0, 255, 0), 3)
            cv2.imshow("image", im2)
            cv2.waitKey(0)"""

        return sorted(contours, key=cv2.contourArea, reverse=True)

    def trace(self, scan_type,start, end, **kwargs):
        if not start:
            start = 0
        if not end:
            end = self.num_frames-1
        print(start, end)
        # Validate trace options
        print(scan_type, **kwargs)
        if scan_type == "single":
            min_thresh = kwargs["min_thresh"]
            if min_thresh > 255 or min_thresh < 0:
                print("Minimum thresh value not in range 0 -> 255")
                return
        else:
            num_scans = kwargs["num_scans"]
            offset_initial = kwargs["offset_initial_scan"]
            if num_scans > 15 or num_scans < 2:
                print("Minimum thresh value not in range 0 -> 255")
                return
            if offset_initial < 0 or offset_initial > 100:
                print("Initial offset value not in range 0 -> 100")
                return

        # Trace each frame in video
        for frame in range(int(start), int(end) + 1):
            print("tracing frame #%d"%frame)
            self.vid_cap.set(cv2.CAP_PROP_POS_MSEC, (frame-1) * 67)
            success, frame = self.vid_cap.read()
            filepathJPG = self.folder_path + "/frame%d.jpg" % frame
            cv2.imwrite(filepathJPG, frame)
            if scan_type == "single":
                contours = self.img2ContoursThresh(filepathJPG, kwargs["min_thresh"])
                self.polygons_handler.polygons = map(lambda cnt:Polygon(cnt, "#ffffff"), contours)
                self.polygons_handler.write_new(False, frame)
            else:
                contours = self.img2ContoursMult(
                    filepathJPG,
                    kwargs["num_scans"],
                    kwargs["offset_initial_scan"],
                    kwargs["offset_final_scan"]
                )
                self.polygons_handler.polygons = map(lambda cnt: Polygon(cnt, "#ffffff"), contours)
                self.polygons_handler.write_new(True, frame)
