from GUI.gui import GUI
from tracked_polygons_handler import TrackedPolygonsHandler
from video_vectorizer import VideoTracer
from polygons_handler import PolygonsHandler
import cv2
import glob
from tkinter import messagebox
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import os
import re
from util import get_min_max_frame


# TODO: Add context menu, which lets you select one shape as the start, and another as the end end.
# TODO: Make an auto fill tool and make a regular fill tool.
# Done

class Driver:
    def __init__(self, vid_filepath, project_name):
        # User defined variables
        self.vid_filepath = vid_filepath
        self.project_name = project_name

        # Initialize variables
        self.vid_width = 0
        self.vid_height = 0
        self.vid_cap = None
        self.frame = None
        self.vid_frame_count = 0
        self.rootDir = ""
        self.folder_path = ""
        self.gui = None
        self.min_frame = None
        self.max_frame = None
        self.current_tool = None

        # create object instances
        self.polygons_handler = PolygonsHandler(
            self.folder_path,
            self.vid_width,
            self.vid_height
        )

        self.video_tracer = VideoTracer(
            self.folder_path,
            self.vid_cap,
            (self.vid_width, self.vid_height),
            self.vid_frame_count,
        )

        self.tracked_polygons_handler = TrackedPolygonsHandler(
            self.folder_path
        )

    def setup(self):
        self.init_video()
        self.create_data_folder()
        self.create_frames_folder()
        self.gui = GUI(self)

        if self.min_frame is not None:
            self.gui.update_frame_num_entry(self.frame)
            self.show_image()
        self.gui.start()

    def init_video(self):
        # Get the video and video properties
        self.vid_cap = cv2.VideoCapture(self.vid_filepath)
        self.vid_width = self.vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.vid_height = self.vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.vid_frame_count = int(self.vid_cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def create_data_folder(self):
        # If data folder doesn't exist create it
        self.rootDir = "./data/%s" % self.project_name
        if not os.path.exists(self.rootDir):
            os.makedirs(self.rootDir)

    def create_frames_folder(self):
        # If frames folder doesn't exist create it
        if not os.path.exists("%s/frames" % self.rootDir):
            os.makedirs("%s/frames" % self.rootDir)

        # Find out the num of the most recent frame folder if it doesn't exist create it
        frame_folders = glob.glob("%s/frames/frames_??" % self.rootDir)
        if frame_folders:
            folderNum = int(max(frame_folders)[-2:])
        else:
            folderNum = 1
            os.makedirs("%s/frames/frames_01" % self.rootDir)
        self.folder_path = self.rootDir + "/frames/frames_" + str(folderNum).zfill(2)

        self.min_frame, self.max_frame = get_min_max_frame(self.folder_path)
        self.frame = self.min_frame

    def show_image(self):
        # Gets frame data and draws polygons to screen
        self.tracked_polygons_handler.read()
        self.polygons_handler.read(self.frame)
        tracked_poly_data_dict = self.tracked_polygons_handler.get_tracked_poly_data_dict(self.frame)
        self.gui.draw_polygons(self.polygons_handler.polygons, tracked_poly_data_dict)

    def trace_video(self, *args):
        self.video_tracer.trace(*args)
        self.min_frame = int(args[1])
        self.max_frame = int(args[2])
        self.frame = self.min_frame
        self.show_image()

    def render_video(self, start, end, title, skip_conversion):
        # Render video from frames with options

        outVidName = self.rootDir + title + ".mp4"
        if start < 1 or end > self.max_frame:
            print("frame out of bound")
            #TODO: add popup.show_warning() function so a warning with the above message can be called
            return

        # if skip_conversion is not true, each svg will be converted first to a png.
        if not skip_conversion:
            for i in range(start, end + 1):
                drawing = svg2rlg(self.folder_path + "/frame%d.svg" % i)
                renderPM.drawToFile(drawing, self.folder_path+ "/frame%d.png" % i, fmt="PNG")

        # we create a dictionary storing all the image file names
        images = {}
        for img in os.listdir(self.folder_path):
            if img.endswith(".png"):
                file_num = int(re.sub("[^0-9]", "", img))
                if start <= file_num <= end:
                    images[file_num] = img

        fourcc = cv2.VideoWriter_fourcc('M', 'P', '4', 'V')
        video = cv2.VideoWriter(outVidName, fourcc, 15, (int(self.vid_width), int(self.vid_height)), True)
        for key, image in sorted(images.items()):
            video.write(cv2.imread(os.path.join(self.folder_path, image)))

        cv2.destroyAllWindows()
        video.release()
        self.show_image()

    def next_frame(self):
        self.set_frame(1, is_rel=True)

    def prev_frame(self):
        self.set_frame(-1, is_rel=True)

    def set_frame(self, frame_num, is_rel=False):
        # set frame to the given frame_num, or increment by the frame_num
        if self.frame:
            if is_rel:
                new_frame = self.frame + frame_num
            else:
                new_frame = frame_num

            if self.min_frame is not None and self.min_frame <= new_frame <= self.max_frame:
                self.frame = new_frame
                self.show_image()

            self.gui.update_frame_num_entry(self.frame)

        self.show_image()

    def clear_frames(self, s_frame, e_frame):
        result = messagebox.askyesno("Reset All", "Are you sure?\nThere is no way to undo this", icon='warning')
        if result:
            self.tracked_polygons_handler.clear_tracked_polygons_in_range(s_frame, e_frame)
            self.polygons_handler.set_polygons_white_in_range(s_frame, e_frame)
            self.show_image()

    def gen_tracked_polygons(self):
        self.tracked_polygons_handler.generate_tracked_polygons(self.min_frame, self.max_frame, self.polygons_handler)
        self.tracked_polygons_handler.write()
        self.show_image()

    def save(self):
        self.tracked_polygons_handler.write()


if __name__ == '__main__':
    vid_filepath = r"C:\Users\Joe\OneDrive\Documents\youtube\Asdf12_full\asdfmovie12.mp4"
    project_name = "asdf12"

    driver = Driver(vid_filepath, project_name)
    driver.setup()
