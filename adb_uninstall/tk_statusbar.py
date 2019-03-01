import tkinter as tk


class MultiStatusBar(tk.Frame):
    """
    code from idlelib.MultiStatusBar.MultiStatusBar
    """

    def __init__(self, master, **kw):
        tk.Frame.__init__(self, master, **kw)
        self.labels = {}

    def set_label(self, name, text="", side=tk.LEFT):
        if name not in self.labels:
            label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W)
            label.pack(side=side)
            self.labels[name] = label
        else:
            label = self.labels[name]
        label.config(text=text)
