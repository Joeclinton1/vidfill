from tkinter import *


def create_entry(frame, width=100, initial_value=""):
    entry = Entry(frame, width=width)
    entry.pack()
    entry.insert(0, initial_value)
    return entry


class Popup:
    def __init__(self, root, gui):
        self.gui = gui
        self.driver = gui.driver
        self.root = root
        self.trace_options = {}
        self.trace_options_frame = None

    def popup_handler(self, destroy, cmd):
        cmd()
        destroy()
        self.trace_options = None

    def clear_cpoints(self):
        # create reset popup

        popup = Toplevel(master=self.root, padx=50, pady=10)
        popup.title = "Choose frames"

        Message(popup, text="choose the start and end frame to delete from", width=300).pack()
        start = Entry(popup, width=50)
        start.pack()
        end = Entry(popup, width=50)
        end.pack()

        cmd = lambda: self.popup_handler(
            popup.destroy,
            self.driver.clear_frames(start.get(), end.get())
        )
        Button(popup, text="Clear Frames", command=cmd).pack()

    def trace_video(self):
        popup = Toplevel(master=self.root, padx=50, pady=10)
        popup.title = "Choose frames"

        Message(popup, text="Choose the start and end frame to trace from.\n(Leave form blank to convert entire video)",
                width=300).pack()
        start = Entry(popup, width=50)
        start.pack()
        # start.insert(0, str(frame))
        end = Entry(popup, width=50)
        end.pack()

        scanType = StringVar()
        scanType.set("single")

        cmd_single = lambda: self.insert_trace_options("single", popup)
        cmd_mult = lambda: self.insert_trace_options("mult", popup)
        Radiobutton(popup, text="Single Scan", variable=scanType, value="single", command=cmd_single).pack(anchor=W)
        Radiobutton(popup, text="Multiple scans", variable=scanType, value="mult", command=cmd_mult).pack(anchor=W)
        self.insert_trace_options("single", popup)

        cmd = lambda: self.popup_handler(popup.destroy, self.driver.trace_video(
            scanType=scanType.get(),
            start=start.get(),
            end=end.get(),
            **{k: v.get() for k, v in self.trace_options.items()}
        ))
        Button(popup, text="Trace Video", command=cmd).pack()

    def insert_trace_options(self, type, popup):
        # remove old trace options from trace options frame.
        if self.trace_options_frame:
            for child in self.trace_options_frame.winfo_children():
                child.destroy()
        else:
            self.trace_options_frame = Frame(popup)

        frame = self.trace_options_frame

        self.trace_options = {}
        if type == "single":
            Message(frame, text="Min Threshold value", width=300).pack()
            self.trace_options["min threshold"] = create_entry(frame, width=10, initial_value="7")

        elif type == "mult":
            Message(frame, text="Number of scans", width=300).pack()
            self.trace_options["num scans"] = create_entry(frame, width=15, initial_value="7")

            Message(frame, text="Offset of initial scan", width=300).pack()
            self.trace_options["offset initial scan"] = create_entry(frame, width=8, initial_value="12")

            Message(frame, text="Offset of final scan", width=300).pack()
            self.trace_options["offset final scan"] = create_entry(frame, width=8, initial_value="15")

        frame.pack()

    def convert_to_video(self):
        popup = Toplevel(master=self.root, padx=50, pady=10)
        popup.title = "Choose frames"

        Message(popup,
                text="Choose the start and end frame to convert from.\n(Leave form blank to convert entire video)",
                width=300).pack()
        start = Entry(popup, width=25)
        start.pack()
        end = Entry(popup, width=25)
        end.pack()
        Message(popup, text="Video title:", width=200).pack()
        title = Entry(popup, width=25)
        title.pack()
        skip = IntVar()
        Checkbutton(popup, text="Skip converting svg to png", variable=skip).pack()

        cmd = lambda: self.popup_handler(popup.destroy, self.driver.render_video(
            start=start,
            end=end,
            title=title,
            skip_conversion=skip
        ))
        Button(popup, text="Convert Video", command=cmd).pack()
