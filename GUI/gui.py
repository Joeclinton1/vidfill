from GUI.popup import Popup
from GUI.polygon import InteractiveTimePositionedPolygon
from GUI.toolbar_btn import ToolbarButton
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

        # Init frame variables
        self.frame_num_entry = None

        # init object dictionaries
        self.i_polygons = {}
        self.toolbar_btns = {}

        # Run setup
        self.setup()
        self.toolbar_btns = {}

    def setup(self):
        self.root.geometry("%dx%d+0+0" % (self.s_width, self.s_height))

        # Create menu
        self.menubar = Menu(self.root)
        for label in ["Save", "Print Keyframes", "Clear Frames", "Trace Video", "Generate Keyframes", "Render Video"]:
            self.menubar.add_command(label=label, command=lambda: self.handle_menubar_cmds(label))

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
        self.root.bind('<Left>', self.driver.prev_frame)
        self.root.bind('<Right>', self.driver.next_frame)

        dialogRoot = Toplevel()
        dialogRoot.geometry("%dx%d%+d%+d" % (50, 50, self.s_width / 2 - 300, self.s_height / 2 - 200))
        dialogRoot.withdraw()

        # Configure root
        self.root.config(menu=self.menubar)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def handle_menubar_cmds(self, cmd):
        self.commands = {
            "Save": self.driver.keyframes.write,
            "Print Keyframes": lambda: print(self.driver.keyframes.key_frames),
            "Clear Frames": self.popup.clear_cpoints,
            "Trace Video": self.popup.trace_video,
            "Generate Keyframes": lambda: self.driver.gen_keyframes,
            "Render Video": self.popup.convert_to_video
        }

        self.commands[cmd]()

    def timeline_entry_return(self):
        frame_num = int(self.frame_num_entry.get())
        self.driver.set_frame(frame_num, is_rel=False)
        self.root.focus_set()

    def start(self):
        self.root.mainloop()

    def draw_polygons(self, polygons, cnt_time_pos_dict):
        # Free up memory by deleting old polygons
        active_shape_id = None
        for id, i_poly in self.i_polygons.items():
            if i_poly.active:
                active_shape_id = id
        self.canvas.delete("all")
        for i_polygon in self.i_polygons:
            del i_polygon
        self.i_polygons = {}

        # Create new polygons
        for cnt_id, polygon, fill in polygons:
            if cnt_id in cnt_time_pos_dict:
                time_pos = cnt_time_pos_dict[cnt_id][0]
                shape_id = cnt_time_pos_dict[cnt_id][1]
            else:
                time_pos = None
                shape_id = None
            scaled_pts = [self.scale * pt for pt in polygon]

            i_polygon = InteractiveTimePositionedPolygon(
                id=shape_id,
                gui=self,
                active=active_shape_id == shape_id,
                vertices=scaled_pts,
                time_pos=time_pos,
                fill="#" + fill,
                outline='#000000'
            )
            self.i_polygons[shape_id] = i_polygon

    def update_frame_num_entry(self, frame):
        self.frame_num_entry.delete(0, END)
        self.frame_num_entry.insert(0, frame)

    def changeTool(self, icon):
        self.current_tool = icon
        print(icon)

    def on_closing(self):
        self.driver.keyframes.write()
        self.root.destroy()
