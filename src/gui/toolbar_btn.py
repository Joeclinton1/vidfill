from tkinter import Button


class ToolbarButton(Button):
    def __init__(self, gui, icon_name, **kw):
        Button.__init__(self, **kw)
        self.icon_name = icon_name
        self.gui = gui
        self.driver = gui.driver
        self.defaultBackground = self["background"]
        self.active = False
        self.bind("<Button-1>", self.on_click)
        # self.bind("<Enter>", self.on_enter)
        # self.bind("<Leave>", self.on_leave)

    def on_click(self, e):
        self.active = True
        self['background'] = self['activebackground']

        # Set siblings to inactive
        for icon_name in self.gui.toolbar_btns:
            if self.icon_name != icon_name:
                btn = self.gui.toolbar_btns[icon_name]
                btn.configure(bg='#F0F0F0')
                btn.active = False

        # Set current tool to this
        self.driver.current_tool = self.icon_name

    def on_enter(self, e):
        self['background'] = self['activebackground']

    def on_leave(self, e):
        if not self.active:
            self['background'] = self.defaultBackground