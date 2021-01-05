from GUI.gui import GUI
from keyframes import Keyframes
from video_vectorizer import VideoTracer
from contours import Contours
import cv2
import glob
import os
from tkinter import messagebox


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
        self.keyframes = None
        self.gui = None
        self.video_tracer = None
        self.contours = None
        self.commands = {}
        self.min_frame = None
        self.max_frame = None

    def setup(self):
        self.init_video()
        self.create_data_folder()
        self.create_frames_folder()
        self.init_classes()
        self.define_commands()
        self.gui = GUI(self.vid_height, self.commands)

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

        svg_frames = glob.glob("%s/frame*.svg" % self.folder_path)
        if svg_frames:
            self.min_frame = int(min(svg_frames).split("\\")[-1][5:-4])
            self.max_frame = max([int(a.split("\\")[-1][5:-4]) for a in svg_frames])
            self.frame = self.min_frame

    def show_image(self):
        # Gets frame data and draws polygons to screen
        self.keyframes.read()
        self.contours.read(self.frame)
        cnt_time_pos_dict = self.keyframes.get_cnt_time_pos_dict(self.frame)
        self.gui.draw_polygons(self.contours.tk_polygons, cnt_time_pos_dict)

    def init_classes(self):
        self.keyframes = Keyframes(
            self.folder_path
        )

        self.contours = Contours(
            self.folder_path,
            self.vid_width,
            self.vid_height
        )
        self.video_tracer = VideoTracer(
            self.folder_path,
            self.vid_cap,
            (self.vid_width, self.vid_height),
            self.vid_frame_count,
            self.contours.write_new
        )

    def define_commands(self):
        def refresh_after(func):
            func()
            self.show_image()

        self.commands = {
            "save cpoints": self.keyframes.write,
            "print keyframes": lambda: print(self.keyframes.key_frames),
            "clear frames": lambda: refresh_after(self.clear_frames),
            "trace video": lambda *args: self.trace_video(*args),
            "set frame": lambda num_frames, is_rel: self.set_frame(num_frames, is_rel),
            "gen keyframes": lambda: refresh_after(self.gen_keyframes)
        }

    def trace_video(self, *args):
        self.video_tracer.trace(*args)
        self.min_frame = int(args[1])
        self.max_frame = int(args[2])
        self.frame = self.min_frame
        self.show_image()

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

    def clear_frames(self, s_frame, e_frame):
        result = messagebox.askyesno("Reset All", "Are you sure?\nThere is no way to undo this", icon='warning')
        if result:
            self.keyframes.clear_cpoints_in_range(s_frame, e_frame)
            self.contours.clear_contours_in_range(s_frame, e_frame)
            self.show_image()

    def gen_keyframes(self):
        key_frames = self.contours.track_contours(self.min_frame, self.max_frame)
        self.keyframes.key_frames = key_frames
        self.keyframes.write()


if __name__ == '__main__':
    vid_filepath = r"C:\Users\Joe\OneDrive\Documents\youtube\Asdf12_full\asdfmovie12.mp4"
    project_name = "asdf12"

    driver = Driver(vid_filepath, project_name)
    driver.setup()
