from GUI.popup import Popup
from GUI.interactive_polygon import InteractiveTimePositionedPolygon
from GUI.toolbar_btn import ToolbarButton
from GUI.point_path import PointPath
from tkinter import *
from tkinter import Tk
from tkinter import Canvas
import os


class GUI:
    def __init__(self, driver):
        # Create driver reference
        self.driver = driver

        # Init GUI roots
        self.root = Tk()
        self.menubar = None
        self.popup = Popup(self.root, self)
        self.canvas = None

        # Define Screen dimensions
        self.s_width = self.root.winfo_screenwidth()
        self.s_height = self.root.winfo_screenheight()
        self.s_pad = 200
        self.scale = (self.s_height - self.s_pad) / driver.vid_height

        # Setup icons dictionary
        self.icons = {}
        for filename in os.listdir("./GUI/icons"):
            icon_name = filename.split('.')[0]
            self.icons[icon_name] = PhotoImage(file="./GUI/icons/" + filename)

        # init object dictionaries
        self.i_polygons = {}
        self.point_paths = {}
        self.toolbar_btns = {}

        # Menubar commands
        self.menubar_cmds = {
            "Save": self.driver.save,
            "Print tracked_polygons": self.driver.tracked_polygons_handler.print_tracked_polygons,
            "Clear Frames": self.popup.clear_cpoints,
            "Trace Video": self.popup.trace_video,
            "Generate tracked_polygons": self.driver.gen_tracked_polygons,
            "Render Video": self.popup.convert_to_video
        }

        # other variables
        self.frame_num_entry = None
        self.active_tracked_poly_id = None
        self.is_touching_point = False

        # Run setup
        self.setup()
        self.toolbar_btns = {}

    def setup(self):
        self.root.geometry("%dx%d+0+0" % (self.s_width, self.s_height))

        # Create menu
        self.menubar = Menu(self.root)
        for label in ["Save", "Print tracked_polygons", "Clear Frames", "Trace Video", "Generate tracked_polygons",
                      "Render Video"]:
            self.menubar.add_command(label=label, command=lambda l=label: self.menubar_cmds[l]())

        # Create toolbar
        toolbar = Frame(self.root)
        # Create toolbar buttons
        for icon_name, image in self.icons.items():
            if icon_name not in ["lArrow", "rArrow"]:
                button = ToolbarButton(
                    gui=self,
                    icon_name=icon_name,
                    master=toolbar,
                    image=image,
                    activebackground='#42cef4',
                )
                self.toolbar_btns[icon_name] = button
                button.image = image
                button.pack(pady=5, padx=2)
        toolbar.pack(side=LEFT)

        # Create canvas
        self.canvas = Canvas(self.root, width=self.s_width - self.s_pad / 1.5,
                             height=self.s_height - self.s_pad)
        self.canvas.pack(anchor='s', pady=20)
        self.root.bind("<r>", lambda event: self.root.focus_set())

        # create timeline buttons
        timeline = Frame(self.root, takefocus=0)
        Button(timeline, image=self.icons['lArrow'], command=self.driver.prev_frame).pack(side=LEFT)
        self.frame_num_entry = Entry(timeline, justify='center', takefocus=0)
        self.frame_num_entry.bind("<Return>", self.timeline_entry_return)
        self.frame_num_entry.pack(side=LEFT, padx=10)
        Button(timeline, image=self.icons['rArrow'], command=self.driver.next_frame).pack(side=LEFT)
        timeline.pack(pady=5)
        self.root.bind('<Left>', lambda e: self.driver.prev_frame())
        self.root.bind('<Right>', lambda e: self.driver.next_frame())

        dialogRoot = Toplevel()
        dialogRoot.geometry("%dx%d%+d%+d" % (50, 50, self.s_width / 2 - 300, self.s_height / 2 - 200))
        dialogRoot.withdraw()

        # Configure root
        self.root.config(menu=self.menubar)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def timeline_entry_return(self):
        frame_num = int(self.frame_num_entry.get())
        self.driver.set_frame(frame_num, is_rel=False)
        self.root.focus_set()

    def start(self):
        self.root.mainloop()

    @staticmethod
    def tk_polygon_from_cnt(cnt):
        return [item for sublist in cnt for item in sublist]

    def draw(self, polygons, tracked_poly_data):
        self.canvas.delete("all")
        self.create_point_paths(tracked_poly_data)
        self.create_polygons(polygons, tracked_poly_data)
        for point_path in self.point_paths.values():
            point_path.bring_to_front()

    def create_point_paths(self, tracked_poly_data):
        # Free up memory by deleting old point paths
        for point_path in self.point_paths:
            del point_path
        self.point_paths = {}

        # Create new point paths
        for id, tracked_poly in tracked_poly_data.items():
            scaled_pts = [[self.scale * val for val in pt] for pt in tracked_poly.path_points]
            point_path = PointPath(
                id=id,
                gui=self,
                points_coords=scaled_pts,
            )
            point_path.hide()

            self.point_paths[id] = point_path

    def create_polygons(self, polygons, tracked_poly_data):
        # Free up memory by deleting old polygons
        for i_polygon in self.i_polygons:
            del i_polygon
        self.i_polygons = {}

        # Create new polygons
        for cnt_id, polygon in polygons.items():
            tk_polygon = self.tk_polygon_from_cnt(polygon.cnt)
            scaled_tk_polygon = [self.scale * pt for pt in tk_polygon]

            if cnt_id in tracked_poly_data:
                time_pos = tracked_poly_data[cnt_id].temporal_label
                tracked_poly_id = tracked_poly_data[cnt_id].tracked_poly_id
            else:
                time_pos = None
                tracked_poly_id = None

            i_polygon = InteractiveTimePositionedPolygon(
                id=tracked_poly_id,
                gui=self,
                active=self.active_tracked_poly_id is not None and self.active_tracked_poly_id == tracked_poly_id,
                vertices=scaled_tk_polygon,
                time_pos=time_pos,
                point_path=self.point_paths[tracked_poly_id],
                fill=polygon.fill,
                outline='#000000'
            )

            self.i_polygons[tracked_poly_id] = i_polygon

    def update_frame_num_entry(self, frame):
        self.frame_num_entry.delete(0, END)
        self.frame_num_entry.insert(0, frame)

    def on_closing(self):
        self.driver.tracked_polygons_handler.write()
        self.root.destroy()
