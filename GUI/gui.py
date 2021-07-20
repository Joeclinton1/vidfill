from GUI.popup import Popup

from tkinter import *
from tkinter import Tk
from tkinter import Canvas
import os


class GUI:
    def __init__(self, vid_height, fireEvent):
        # Init GUI roots
        self.root = Tk()
        self.menubar = None
        self.popup = Popup(self.root, self.fireEvent)
        self.canvas = None

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
        # Init other variables
        self.current_tool = None
        self.fireEvent = fireEvent
        self.i_polygons = {}
        # Run setup
        self.setup()
        self.toolbar_btns = {}

    def setup(self):
        self.root.geometry("%dx%d+0+0" % (self.s_width, self.s_height))

        # Create menu
        self.menubar = Menu(self.root)
        for label in ["Save", "Clear Frames", "Trace Video", "Generate Keyframes", "Render", "Print Keyframes"]:
            self.menubar.add_command(label=label, command=self.fireEvent(GUIEvent("menubar", t=label)))

        # Create toolbar
        toolbar = Frame(self.root)
        # Create toolbar buttons
        for icon_name, image in self.icons.items():
            if icon_name not in ["lArrow", "rArrow"]:
                button = ToolbarButton(icon_name=icon_name, master=toolbar, image=image, activebackground='#42cef4',
                                       command=lambda: self.toolbar_btn_cmd(icon_name))
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
        Button(timeline, image=self.icons['lArrow'], command=self.fireEvent(GUIEvent("timeline", t= "left arrow"))).pack(side=LEFT)
        self.frame_num_entry = Entry(timeline, justify='center', takefocus=0)
        self.frame_num_entry.bind("<Return>", self.fireEvent(GUIEvent("timeline", t= "entry", event_type= "return")))
        self.frame_num_entry.pack(side=LEFT, padx=10)
        Button(timeline, image=self.icons['rArrow'], command= self.fireEvent(GUIEvent("timeline", t= "right arrow"))).pack(side=LEFT)
        timeline.pack(pady=5)
        self.root.bind('<Left>', lambda event: self.fireEvent(GUIEvent("root", event_type= "left")))
        self.root.bind('<Right>', lambda event: self.fireEvent(GUIEvent("root", event_type= "right")))

        dialogRoot = Toplevel()
        dialogRoot.geometry("%dx%d%+d%+d" % (50, 50, self.s_width / 2 - 300, self.s_height / 2 - 200))
        dialogRoot.withdraw()

        # Configure root
        self.root.config(menu=self.menubar)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def toolbar_btn_cmd(self, target_icon_name):
        for icon_name in self.toolbar_btns:
            if target_icon_name != icon_name:
                btn = self.toolbar_btns[icon_name]
                btn.configure(bg='#F0F0F0')
                btn.active = False

        self.fireEvent(GUIEvent("toolbar", t=self.toolbar_btns))

    def polygon_cmd(self, id):
        for poly_id in self.i_polygons:
            if poly_id != id:
                poly = self.i_polygons[poly_id]
                poly.set_outline('#000000', 1)
                poly.active = False

        self.fireEvent(GUIEvent("polygon", t = self.i_polygons[id]))

    def start(self):
        self.root.mainloop()

    def draw_polygons(self, polygons, cnt_time_pos_dict):
        # Free up memory by deleting old polygons
        active_shape_id = None
        for i_poly in self.i_polygons:
            if i_poly.active:
                active_shape_id = i_poly.id
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
                id = shape_id,
                active=active_shape_id == shape_id,
                canvas=self.canvas,
                vertices=scaled_pts,
                time_pos=time_pos,
                command=self.polygon_cmd,
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
        self.fireEvent(GUIEvent("root"), event_type="close")
        self.root.destroy()

class InteractiveTimePositionedPolygon():
    def __init__(self, id, active, canvas, vertices, time_pos, command, **kw):
        self.master = canvas
        self.tag = canvas.create_polygon(vertices, **kw)
        self.active = active
        self.command = command
        self.id = id

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
        self.set_outline(self.active_outline_colour, 2)
        self.active = True
        self.command()

    def on_enter(self, e):
        if not self.active:
            self.set_outline(self.active_outline_colour, 1)

    def on_leave(self, e):
        if not self.active:
            self.set_outline('#000000', 1)


class ToolbarButton(Button):
    def __init__(self, icon_name, **kw):
        Button.__init__(self, **kw)
        self.icon_name = icon_name
        self.defaultBackground = self["background"]
        self.active = False
        self.bind("<Button-1>", self.on_click)
        # self.bind("<Enter>", self.on_enter)
        # self.bind("<Leave>", self.on_leave)

    def on_click(self, e):
        self.active = True
        self['background'] = self['activebackground']

    def on_enter(self, e):
        self['background'] = self['activebackground']

    def on_leave(self, e):
        if not self.active:
            self['background'] = self.defaultBackground


class GUIEvent:
    def __init__(self, loc, event_type="click", t=None):
        self.target = t
        self.type = event_type
        self.location = loc
