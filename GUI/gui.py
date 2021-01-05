from GUI.popup import Popup

from tkinter import *
from tkinter import Tk
from tkinter import Canvas
import os


class GUI:
    def __init__(self, vid_height, commands):
        # Init GUI root
        self.root = Tk()

        # Define Screen dimensions
        self.s_width = self.root.winfo_screenwidth()
        self.s_height = self.root.winfo_screenheight()
        self.s_pad = 200
        self.scale = (self.s_height - self.s_pad) / vid_height

        # Setup icons dictionary
        self.icons = {}
        for filename in os.listdir("./GUI/icons"):
            icon_name = filename.split('.')[0]
            self.icons[icon_name] = PhotoImage(file="./GUI/icons/" + filename)

        # Init frame variables
        self.frame_num_entry = None
        self.set_frame = commands['set frame']

        # Init other variables
        self.current_tool = None
        self.popup = Popup(self.root, commands)
        self.commands = commands
        self.canvas = None
        self.i_polygons = []
        # Run setup
        self.setup()

    def setup(self):
        self.root.geometry("%dx%d+0+0" % (self.s_width, self.s_height))

        # Create menu
        menubar = Menu(self.root)
        menubar.add_command(label="Save", command=self.commands["save cpoints"])
        menubar.add_command(label="Clear Frames", command=self.popup.clear_cpoints)
        menubar.add_command(label="Trace Video", command=self.popup.trace_video)
        menubar.add_command(label= "Generate keyframes", command = self.commands["gen keyframes"])
        menubar.add_command(label="Render", command=self.popup.convert_to_video)
        menubar.add_command(label="Print Keyframes", command=lambda: self.commands["print keyframes"])

        # Create toolbar
        toolbar = Frame(self.root)
        toolbar_buttons = []
        # Create toolbar buttons
        for icon_name, image in self.icons.items():
            if icon_name not in ["lArrow", "rArrow"]:
                button = ToolbarButton(toolbar_buttons, toolbar, image=image, activebackground='#42cef4',
                                       command=lambda icon=icon_name: self.changeTool(icon_name))
                toolbar_buttons.append(button)
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
        Button(timeline, image=self.icons['lArrow'], command=self.prev_frame).pack(side=LEFT)
        self.frame_num_entry = Entry(timeline, justify='center', takefocus=0)
        self.frame_num_entry.bind("<Return>", self.go_to_frame)
        self.frame_num_entry.pack(side=LEFT, padx=10)
        Button(timeline, image=self.icons['rArrow'], command=self.next_frame).pack(side=LEFT)
        timeline.pack(pady=5)
        self.root.bind('<Left>', lambda event: self.prev_frame())
        self.root.bind('<Right>', lambda event: self.next_frame())

        dialogRoot = Toplevel()
        dialogRoot.geometry("%dx%d%+d%+d" % (50, 50, self.s_width / 2 - 300, self.s_height / 2 - 200))
        dialogRoot.withdraw()

        # Configure root
        self.root.config(menu=menubar)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start(self):
        self.root.mainloop()

    def draw_polygons(self, polygons, cnt_time_pos_dict):
        # Free up memory by deleting old polygons
        active_shape_id = None
        for i_poly in self.i_polygons:
            if i_poly.active:
                active_shape_id = i_poly.shape_id

        self.canvas.delete("all")
        for i_polygon in self.i_polygons:
            del i_polygon
        self.i_polygons = []
        for cnt_id, polygon, fill in polygons:
            if cnt_id in cnt_time_pos_dict:
                time_pos = cnt_time_pos_dict[cnt_id][0]
                shape_id = cnt_time_pos_dict[cnt_id][1]
            else:
                time_pos = None
                shape_id = None
            scaled_polygon = [self.scale * pt for pt in polygon]
            i_polygon = InteractivePolygon(shape_id, active_shape_id, self.canvas, scaled_polygon, self.i_polygons, time_pos, fill="#" + fill, outline='#000000')
            self.i_polygons.append(i_polygon)

    def update_frame_num_entry(self, frame):
        self.frame_num_entry.delete(0, END)
        self.frame_num_entry.insert(0, frame)

    def changeTool(self, icon):
        self.current_tool = icon
        print(icon)

    def on_closing(self):
        self.commands["save cpoints"]()
        self.root.destroy()

    def next_frame(self):
        self.set_frame(1, is_rel=True)

    def prev_frame(self):
        self.set_frame(-1, is_rel=True)

    def go_to_frame(self):
        frame_num = int(self.frame_num_entry.get())
        self.set_frame(frame_num, is_rel=False)
        self.root.focus_set()


class InteractivePolygon():
    def __init__(self, shape_id, active_shapeid, canvas, polygon, siblings, time_pos, **kw):
        self.master = canvas
        self.tag = canvas.create_polygon(polygon, **kw)
        self.siblings = siblings
        self.active = (True if active_shapeid == shape_id else False)
        self.shape_id = shape_id
        self.active_shape_id = active_shapeid
        canvas.tag_bind(self.tag, "<Button-1>", self.on_click)
        canvas.tag_bind(self.tag, "<Enter>", self.on_enter)
        canvas.tag_bind(self.tag, "<Leave>", self.on_leave)

        outline_colours = {
            'start': '#00FF00',  # green
            'middle': '#FFA500',  # orange
            'end': '#FF0000'  # red
        }
        if time_pos:
            self.active_outline_colour = outline_colours[time_pos]
        else:
            self.active_outline_colour = '#0000FF'

        if self.active:
            self.set_outline(self.active_outline_colour, 2)

    def set_outline(self, colour, width):
        self.master.itemconfig(self.tag, outline=colour, width=width)

    def on_click(self, e):
        for sibling in self.siblings:
            sibling.set_outline('#000000', 1)
            sibling.active = False

        self.set_outline(self.active_outline_colour, 2)
        self.active = True
        self.active_shape_id = self.shape_id
        print(self.shape_id)

    def on_enter(self, e):
        if not self.active:
            self.set_outline(self.active_outline_colour, 1)

    def on_leave(self, e):
        if not self.active:
            self.set_outline('#000000',1)


class ToolbarButton(Button):
    def __init__(self, siblings, master, **kw):
        Button.__init__(self, master=master, **kw)
        self.defaultBackground = self["background"]
        self.clicked = False
        self.bind("<Button-1>", self.on_click)
        self.siblings = siblings
        # self.bind("<Enter>", self.on_enter)
        # self.bind("<Leave>", self.on_leave)

    def on_click(self, e):
        self.clicked = True
        for button in self.siblings:
            button.configure(bg='#F0F0F0')
        self['background'] = self['activebackground']

    def on_enter(self, e):
        self['background'] = self['activebackground']

    def on_leave(self, e):
        if not self.clicked:
            self['background'] = self.defaultBackground
