from tkinter import *
from tkinter import messagebox


class Popup:
    def __init__(self, root, commands):
        self.root = root
        self.commands = commands
        self.trace_options = None

    def popup_handler(self, cmd, destroy, *args):
        args = [arg.get() for arg in args]
        self.commands[cmd](*args)
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
        cmd = lambda: self.popup_handler("clear cpoints", popup.destroy, start, end)
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

        cmd1 = lambda: self.insert_trace_options("single", popup)
        cmd2 = lambda: self.insert_trace_options("mult", popup)
        Radiobutton(popup, text="Single Scan", variable=scanType, value="single", command=cmd1).pack(anchor=W)
        Radiobutton(popup, text="Multiple scans", variable=scanType, value="mult", command=cmd2).pack(anchor=W)
        self.insert_trace_options("single", popup)

        cmd3 = lambda: self.popup_handler(
            "trace video",
            popup.destroy,
            scanType,
            start,
            end,
            *self.trace_options[1:],
        )
        Button(popup, text="Trace Video", command=cmd3).pack()

    def insert_trace_options(self, type, popup):
        if self.trace_options:
            for child in self.trace_options[0].winfo_children():
                child.destroy()
        else:
            self.trace_options = [Frame(popup)]

        frame = self.trace_options[0]
        options = []
        if type == "single":
            Message(frame, text="Min Threshold value", width=300).pack()
            options.append(Entry(frame, width=10))
            options[-1].pack()
            options[-1].insert(0, "150")


        elif type == "mult":
            Message(frame, text="Number of scans", width=300).pack()
            options.append(Entry(frame, width=5))
            options[-1].pack()
            options[-1].insert(0, "7")

            Message(frame, text="Offset of initial scan", width=300).pack()
            options.append(Entry(frame, width=8))
            options[-1].pack()
            options[-1].insert(0, "12")

            Message(frame, text="Offset of final scan", width=300).pack()
            options.append(Entry(frame, width=8))
            options[-1].pack()
            options[-1].insert(0, "15")

        self.trace_options.extend(options)
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
        cmd = lambda: self.popup_handler(
            "convert to video",
            popup.destroy,
            start,
            end,
            title,
            skip,
        )
        Button(popup, text="Convert Video", command=cmd).pack()
