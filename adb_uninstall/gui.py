#!/usr/bin/env python3

"""
    Deinstall bloatware apps via adb without root.


    See also:
        de: https://www.kuketz-blog.de/android-system-apps-ohne-root-loeschen/
        en: https://forum.xda-developers.com/honor-6x/how-to/guide-list-bloat-software-emui-safe-to-t3700814

    :created: 05.02.2019 by Jens Diemer
    :copyleft: 2019 by Jens Diemer
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import logging
import subprocess
import sys
import time
import webbrowser

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    from tkinter.scrolledtext import ScrolledText
except ImportError as err:
    print("\nERROR can't import Tkinter: %s\n" % err)
    print("Hint: 'apt install python3-tk'\n")
    sys.exit(-1)


from adb_uninstall import __version__

log = logging.getLogger(__name__)

GOOGLE_PLAY_URL = "https://play.google.com/store/apps/details?id=%s"
COLOR_LIGHT_GREEN = "#e0ffe0"
COLOR_LIGHT_RED = "#ffe0e0"
OUTPUT_FILE = "packages.html"


def verbose_check_output(*args):
    """ 'verbose' version of subprocess.check_output() """
    log.info("Call: %r" % " ".join(args))
    output = subprocess.check_output(args, universal_newlines=True, stderr=subprocess.STDOUT)
    return output


def verbose_check_call(*args):
    """ 'verbose' version of subprocess.check_call() """
    print("\tCall: %r\n" % " ".join(args))
    subprocess.check_call(args, universal_newlines=True)


def iter_subprocess_output(*args, timeout=10):
    cmd = " ".join(args)
    print("\tCall: %r\n" % cmd)
    proc = subprocess.Popen(args, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    end_time = time.time() + timeout
    for line in iter(proc.stdout.readline, ""):
        yield line

        if time.time() > end_time:
            raise subprocess.TimeoutExpired(args, timeout)

    timeout = end_time - time.time()
    if timeout < 1:
        timeout = 1

    outs, errs = proc.communicate(timeout=timeout)
    for line in outs:
        yield line

    if proc.returncode:
        raise subprocess.CalledProcessError(returncode=proc.returncode, cmd=cmd)


def automenu(master, menudata):
    def prepstr(label, used):
        """
        Based on prepstr() from python/Lib/idlelib/EditorWindow.py
        Helper to extract the underscore from a string, e.g.
        prepstr("Co_py") returns (2, "Copy").
        Check if the used character is unique in the menu part.
        """
        i = label.find("_")
        if i >= 0:
            label = label[:i] + label[i + 1 :]

            char = label[i]
            assert char not in used, ("underline %r used in %r is not unique in this menu part!") % (char, label)
            used.append(char)

        return i, label

    # Add a menubar to root
    menubar = tk.Menu(master)
    master.config(menu=menubar)

    used_topunderline = []
    for toplabel, menuitems in menudata:
        # add new main menu point
        menu = tk.Menu(menubar, tearoff=False)
        underline, toplabel = prepstr(toplabel, used_topunderline)
        menubar.add_cascade(label=toplabel, menu=menu, underline=underline)

        # add all sub menu points
        used_underlines = []
        for index, menudata in enumerate(menuitems):
            if not menudata:
                menu.add_separator()
                continue

            label, keycode, command = menudata

            underline, label = prepstr(label, used_underlines)

            menu.add_command(label=label, underline=underline, command=command)
            if keycode:
                menu.entryconfig(index, accelerator=keycode)
                master.bind("<" + keycode + ">", command)


class Package:
    KEEP = "keep"
    REMOVE = "remove"

    def __init__(self, *, package_name, index, action=None):
        self.package_name = package_name
        self.index = index

        if action is None:
            self.action = self.KEEP
        else:
            assert action in (self.KEEP, self.REMOVE)
            self.action = action

    @property
    def keep(self):
        return self.action == self.KEEP

    @property
    def remove(self):
        return self.action == self.REMOVE

    def set_keep(self):
        self.action = self.KEEP

    def set_remove(self):
        self.action = self.REMOVE

    def open_play_google(self):
        webbrowser.open_new_tab(GOOGLE_PLAY_URL % self.package_name)

    def __str__(self):
        return "%i %r %r" % (self.index, self.action, self.package_name)

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.__str__())


class Packages:
    def __init__(self):
        self.name2package = {}
        self.index2package = {}

    def add(self, *, package_name, action=None):
        index = len(self.name2package)

        package = Package(package_name=package_name, index=index, action=action)

        self.name2package[package_name] = package
        self.index2package[index] = package

    def get_by_index(self, *, index):
        return self.index2package[index]

    def apply(self, out):
        for package in self.index2package.values():
            if package.remove:
                package_name = package.package_name
                out("Remove: %r" % package_name)

                try:
                    for line in iter_subprocess_output(
                        "adb", "shell", "pm", "uninstall", "--user", "0", package_name, timeout=3
                    ):
                        out(line)
                except subprocess.CalledProcessError as err:
                    out("ERROR: %s" % err)


class ScrollableTreeview(ttk.Frame):
    def __init__(self, *, parent, columns, call_back, **kwargs):
        self.parent = parent
        self.call_back = call_back
        super().__init__(parent, **kwargs)

        self.row_count = 0

        self.tree = ttk.Treeview(self, columns=columns)
        self.tree.bind("<ButtonRelease-1>", self._call_back)

        for no, column in enumerate(columns):
            self.tree.column("#%i" % no, stretch=True, anchor=tk.CENTER)
            self.tree.heading("#%i" % no, text=column)

        self.scrollbar_x = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.scrollbar_y = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)

        self.tree.configure(xscrollcommand=self.scrollbar_x.set, yscrollcommand=self.scrollbar_y.set)

        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.scrollbar_x.grid(row=1, column=0, sticky=tk.EW)
        self.scrollbar_y.grid(row=0, column=1, sticky=tk.NS)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.tree.columnconfigure(0, weight=1)
        self.tree.rowconfigure(0, weight=1)

    def row2tagname(self, row):
        return "row_%i" % row

    def row2index(self, row):
        return ""

    def add(self, *, values):
        # print("add:", values)
        self.tree.insert("", tk.END, tag=self.row2tagname(self.row_count), text=values[0], values=values[1:])
        self.row_count += 1
        return self.row_count - 1

    def _call_back(self, event):
        item = self.tree.focus()
        self.tree.selection_remove(item)
        row = self.tree.index(item)
        column = self.tree.identify_column(event.x)
        self.call_back(item, row, column)

    def set_row_background_color(self, row, color):
        tagname = self.row2tagname(row)
        self.tree.tag_configure(tagname, background=color)

    def set_text(self, *, item, column, text):
        self.tree.set(item, column, text)


class PackageTable(ttk.Frame):
    def __init__(self, parent, adb_packages, output_callback, actions):
        self.parent = parent
        self.adb_packages = adb_packages
        self.output_callback = output_callback

        super().__init__(parent)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.tree = ScrollableTreeview(parent=parent, columns=("Package", "Link", "Action"), call_back=self.call_back)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.tree.columnconfigure(0, weight=1)
        self.tree.rowconfigure(0, weight=1)

        self.button_frame = tk.Frame(parent)
        self.button_frame.grid(row=1, column=0, sticky=tk.NSEW)

        self.buttons = []
        for no, (text, command) in enumerate(actions.items()):
            button = tk.Button(self.button_frame, text=text, command=command)
            button.grid(row=0, column=no, padx=10)
            self.buttons.append(button)

    def add(self, package):
        self.adb_packages.add(package_name=package)
        row = self.tree.add(values=(package, "open play.google.com", "keep"))
        assert isinstance(row, int)

        self.tree.set_row_background_color(row=row, color=COLOR_LIGHT_GREEN)

    def call_back(self, item, row, column):
        print("Clicked:", item, row, column)

        package = self.adb_packages.get_by_index(index=row)
        print(package)

        if column == "#1":
            package.open_play_google()
        elif column in ("#0", "#2"):
            if package.keep:
                package.set_remove()
                self.tree.set_row_background_color(row, color=COLOR_LIGHT_RED)
            elif package.remove:
                package.set_keep()
                self.tree.set_row_background_color(row, color=COLOR_LIGHT_GREEN)
            else:
                raise RuntimeError("?!?")

            self.tree.set_text(item=item, column="#2", text=package.action)


class AdbUninstaller(tk.Tk):
    def __init__(self, width=700):
        super().__init__()
        self.geometry(
            "%dx%d+%d+%d"
            % (
                width,
                self.winfo_screenheight() * 0.4,
                (self.winfo_screenwidth() - width) / 2,
                self.winfo_screenheight() * 0.1,
            )
        )

        self.title("%s (GPL) v%s" % (self.__class__.__name__, __version__))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        menudata = (
            [
                "_File",
                (
                    # ("_New", "Control-n", self.new),
                    # ("_Open...", "Control-o", self.open),
                    # ("_Save", "Control-s", self.dummy),
                    # (),  # Add a separator here
                    ("_Exit", "Alt-F4", self.destroy),
                ),
            ],
            # [
            #     "_Actions",
            #     (
            #         ("_Fetch Package List", "F5", self.fetch),
            #         ("Find", "F3", self.dummy),
            #         ("F_ooBar", "Control-Shift-A", self.dummy),
            #         ("Foo_Bar2", "Alt-s", self.dummy),
            #     ),
            # ],
            [
                "_Help",
                (
                    # ("_Help", "F1", self.dummy),
                    # (),  # Add a separator here
                    ("_About", "", self.about),
                ),
            ],
        )

        # Create menu
        automenu(self, menudata)

        p = ttk.Panedwindow(self, orient=tk.VERTICAL)

        self.list_frame = ttk.Labelframe(p, text="Package List", height=100)
        p.add(self.list_frame)

        self.packages = Packages()

        actions = {
            "list devices": self.list_devices,
            "fetch package": self.fetch,
            "save selection": self.destroy,
            "Apply": self.apply,
            "Exit": self.destroy,
        }

        self.package_table = PackageTable(
            self.list_frame, self.packages, output_callback=self.output_callback, actions=actions
        )
        self.package_table.grid(row=0, column=0, sticky=tk.NSEW)
        self.package_table.columnconfigure(0, weight=1)
        self.package_table.rowconfigure(0, weight=1)

        self.status_frame = ttk.Labelframe(p, text="Status", height=50)
        p.add(self.status_frame)

        self.info_text = ScrolledText(self.status_frame, bg="white", height=10)
        self.info_text.grid(row=0, column=0, sticky=tk.NSEW)
        self.info_text.columnconfigure(0, weight=1)
        self.info_text.rowconfigure(0, weight=1)

        p.grid(row=0, column=0, sticky=tk.NSEW)
        p.columnconfigure(0, weight=1)
        p.rowconfigure(0, weight=1)

        self.origin_stdout_write = sys.stdout.write
        sys.stdout.write = sys.stderr.write = self.stdout_redirect_handler

        print("")

        self.mainloop()

    def output_callback(self, text):
        self.info_text.insert(tk.END, "%s\n" % text)
        self.info_text.see(tk.END)

    def stdout_redirect_handler(self, *args):
        self.origin_stdout_write(*args)

        text = " ".join([str(part) for part in args])
        text = text.rstrip(" \n")
        self.info_text.insert(tk.END, text)
        self.info_text.see(tk.END)

    def apply(self):
        self.packages.apply(out=self.output_callback)

    def list_devices(self):
        self.output_callback("List devices via adb...")
        for line in iter_subprocess_output("adb", "devices", "-l", timeout=3):
            self.output_callback(line)

    def fetch(self, *args):
        self.output_callback("Fetch package list via adb...")

        packages = []
        try:
            for line in iter_subprocess_output("adb", "shell", "pm", "list", "packages"):
                self.output_callback(line)
                if line.startswith("package:"):
                    package_name = line[8:].strip()
                    packages.append(package_name)

        except subprocess.CalledProcessError as err:
            self.output_callback("ERROR: %s" % err)
            return

        for no, package in enumerate(sorted(packages)):
            self.output_callback(package)

            self.package_table.add(package)

    # def new(self, *args):
    #     self.info_text.insert(tk.END, "\nFile/New\n")
    #
    # def open(self, *args):
    #     self.info_text.insert(tk.END, "\nFile/Open\n")

    def about(self, *args):
        messagebox.showinfo(title="about", message="See github page ;)")

    def destroy(self, *args):
        close = messagebox.askyesno(title="close?", message="Quit?")
        if close:
            super().destroy()


def main():
    AdbUninstaller()


if __name__ == "__main__":
    main()
