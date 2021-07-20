from tkinter import *
from tkinter import messagebox
from GUI.gui import GUIEvent


def create_entry(frame, width=100, initial_value=""):
    entry = Entry(frame, width=width)
    entry.pack()
    entry.insert(0, initial_value)
    return entry


class Popup:
    def __init__(self, root, fireEvent):
        self.root = root
        self.fireEvent = fireEvent
        self.trace_options = {}

    def popup_handler(self, destroy, target):
        self.fireEvent(GUIEvent(loc="popup", event_type="submit", t=target))
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
        target = {
            "name": "clear cpoints",
            "start": start,
            "end": end
        }
        cmd = lambda: self.popup_handler(popup.destroy, target)
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

        target = {
            "name": "trace video",
            "scan type": scanType,
            "start": start,
            "end": end,
            "trace options": self.trace_options[1:]
        }
        cmd = lambda: self.popup_handler(popup.destroy, target)
        Button(popup, text="Trace Video", command=cmd).pack()

    def insert_trace_options(self, type, popup):
        if "frame" in self.trace_options:
            for child in self.trace_options["frame"].winfo_children():
                child.destroy()

        frame = Frame(popup)
        self.trace_options = {"frame": frame}
        entries = {}
        if type == "single":
            Message(frame, text="Min Threshold value", width=300).pack()
            entries["min threshold"] = create_entry(frame, width=10, initial_value="7")

        elif type == "mult":
            Message(frame, text="Number of scans", width=300).pack()
            entries["num scans"] = create_entry(frame, width=15, initial_value="7")

            Message(frame, text="Offset of initial scan", width=300).pack()
            entries["offset initial scan"] = create_entry(frame, width=8, initial_value="12")

            Message(frame, text="Offset of final scan", width=300).pack()
            entries["offset final scan"] = create_entry(frame, width=8, initial_value="15")

        self.trace_options["entries"] = entries
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

        target = {
            "name": "convert video",
            "start": start,
            "end": end,
            "title": title,
            "skip conversion": skip
        }
        cmd = lambda: self.popup_handler(popup.destroy, target)
        Button(popup, text="Convert Video", command=cmd).pack()
