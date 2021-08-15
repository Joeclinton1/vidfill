class InteractiveTimePositionedPolygon():
    def __init__(self, id, gui, active, vertices, time_pos, point_path, **kw):
        self.id = id
        self.gui = gui
        self.driver = gui.driver
        self.master = gui.canvas
        self.tag = self.master.create_polygon(vertices, **kw)
        self.active = active
        self.point_path = point_path

        self.master.tag_bind(self.tag, "<Button-1>", self.on_click)
        self.master.tag_bind(self.tag, "<Enter>", self.on_enter)
        self.master.tag_bind(self.tag, "<Leave>", self.on_leave)

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
        self.gui.active_tracked_poly_id = self.id

        # Set siblings to inactive
        for poly_id in self.gui.i_polygons:
            if poly_id != self.id:
                poly = self.gui.i_polygons[poly_id]
                poly.set_outline('#000000', 1)
                poly.active = False

    def on_enter(self, e):
        if not self.active:
            self.set_outline(self.active_outline_colour, 1)

        # show point path
        self.point_path.show()

    def on_leave(self, e):
        if self.gui.is_touching_point:
            print("left")
            return
        print("left 2")
        if not self.active:
            self.set_outline('#000000', 1)

        # hide point path
        self.point_path.hide()
