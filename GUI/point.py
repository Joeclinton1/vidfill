import time


class Point:
    def __init__(self, gui, x, y, fill):
        self.gui = gui
        self.driver = gui.driver
        self.master = gui.canvas
        self.x = x
        self.y = y
        self.r = 5
        self.fill = fill
        self.tag = self.create_circle()
        self.visible = True
        self.hovered = False

        self.master.tag_bind(self.tag, "<Enter>", self.on_enter)
        self.master.tag_bind(self.tag, "<Leave>", self.on_leave)

    def create_circle(self):
        tag = self.master.create_oval(
            self.x - self.r,
            self.y - self.r,
            self.x + self.r,
            self.y + self.r,
            fill=self.fill,
            width=1,
        )
        return tag

    def hide(self):
        self.master.itemconfig(self.tag, fill="", outline="")
        self.visible = False

    def show(self):
        self.master.itemconfig(self.tag, fill=self.fill, outline="black")
        self.visible = True

    def bring_to_front(self):
        self.master.tag_raise(self.tag)

    def on_enter(self, e):
        self.hovered = True
        self.gui.is_touching_point = True

    def on_leave(self, e):
        self.hovered = False
        self.gui.is_touching_point = False
