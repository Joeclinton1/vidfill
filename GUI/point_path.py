from GUI.point import Point


class PointPath:
    def __init__(self, id, gui, points_coords):
        self.id = id
        self.gui = gui
        self.driver = gui.driver
        self.master = gui.canvas
        self.points_coords = points_coords
        self.time_pos_to_fill = {
            'start':  '#00FF00',  # green
            'middle': '#FFA500',  # orange
            'end': '#FF0000'  # red
        }
        self.visible = True

        # lists to hold points and path_tags
        self.points = []
        self.paths_tags = []

        self.setup()

    def setup(self):
        self.create_points(self.points_coords)
        self.create_path(self.points_coords)

    def create_path(self, points_coords):
        prev_point = points_coords[0]
        for point in points_coords[1:]:
            path = self.master.create_line(*prev_point, *point, fill="")
            self.paths_tags.append(path)
            prev_point = point

    def create_points(self, points_coords):
        for i, point in enumerate(points_coords):
            time_pos = 'start' if i == 0 else 'middle' if i < len(points_coords) else 'end'
            fill = self.time_pos_to_fill[time_pos]
            point = Point(gui=self.gui, x=point[0], y=point[1], fill=fill)
            self.points.append(point)

    def hide(self):
        for point in self.points:
            point.hide()
        for path in self.paths_tags:
            self.master.itemconfig(path, fill="")
        self.visible = False

    def show(self):
        for point in self.points:
            point.show()
        for path in self.paths_tags:
            self.master.itemconfig(path, fill="black")
        self.visible = True

    def bring_to_front(self):
        for point in self.points:
            point.bring_to_front()
        for path in self.paths_tags:
            self.master.tag_raise(path)

