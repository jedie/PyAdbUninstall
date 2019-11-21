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
import re
import subprocess
import sys

from adb_uninstall import __version__
from adb_uninstall.adb_package import Package, Packages
from adb_uninstall.constants import COLOR_GREY_RED, COLOR_LIGHT_GREEN, COLOR_LIGHT_RED
from adb_uninstall.tk_automenu import automenu
from adb_uninstall.tk_statusbar import MultiStatusBar
from adb_uninstall.utils.redirect import RedirectStdoutStderr
from adb_uninstall.utils.subprocess2 import verbose_check_output

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    from tkinter.scrolledtext import ScrolledText
except ImportError as err:
    print("\nERROR can't import Tkinter: %s\n" % err)
    print("Hint: 'apt install python3-tk'\n")
    sys.exit(-1)


log = logging.getLogger(__name__)

STATUSBAR_INFO_KEY = "info"
STATUSBAR_DEVICE_KEY = "device"


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

        self.tree.configure(
            xscrollcommand=self.scrollbar_x.set,
            yscrollcommand=self.scrollbar_y.set)

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
        self.tree.insert("", tk.END, tag=self.row2tagname(
            self.row_count), text=values[0], values=values[1:])
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
        self.tree.tag_configure(tagname, background=color, foreground="#000000")

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

        self.tree = ScrollableTreeview(
            parent=parent,
            columns=(
                "Package",
                "Visit Google Play",
                "Visit Exodus Privacy",
                "Action"),
            call_back=self.call_back
        )
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        self.tree.columnconfigure(0, weight=1)
        self.tree.rowconfigure(0, weight=1)

        self.button_frame = tk.Frame(parent)
        self.button_frame.grid(row=1, column=0, sticky=tk.EW)

        self.buttons = []
        for no, (text, command) in enumerate(actions.items()):
            button = tk.Button(self.button_frame, text=text, command=command)
            button.grid(row=0, column=no, padx=10)
            self.buttons.append(button)

    def add(self, package_name):
        package = self.adb_packages.add(package_name=package_name)

        if package.locked:
            info = Package.LOCKED
            color = COLOR_GREY_RED
        else:
            info = Package.KEEP
            color = COLOR_LIGHT_GREEN

        row = self.tree.add(
            values=(package_name, "open play.google.com", "open exodus-privacy.eu.org", info))
        assert isinstance(row, int)

        self.tree.set_row_background_color(row=row, color=color)

    def call_back(self, item, row, column):
        log.debug("Clicked: %r %r %r", item, row, column)

        # FIXME: how to ignore click on table headline items?!?

        package = self.adb_packages.get_by_index(index=row)
        log.debug("Clicked on package: %r", package)

        if column == "#1":
            package.open_play_google()
        elif column == "#2":
            package.open_exodus_privacy()
        elif column in ("#0", "#3"):
            if package.locked:
                print("ignore locked app")
                return

            if package.keep:
                package.set_remove()
                self.tree.set_row_background_color(row, color=COLOR_LIGHT_RED)
            elif package.remove:
                package.set_keep()
                self.tree.set_row_background_color(row, color=COLOR_LIGHT_GREEN)
            else:
                raise RuntimeError("?!?")

            self.tree.set_text(item=item, column="#3", text=package.action)


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

        self.packages = Packages()

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
        self.list_frame.columnconfigure(0, weight=1)
        self.list_frame.rowconfigure(0, weight=1)
        p.add(self.list_frame)

        actions = {
            "list devices": self.list_devices,
            # "fetch package": self.fetch_package_list,
            # "save selection": self.destroy,
            "uninstall apps": self.uninstall_apps,
            "deactivate apps": self.deactivate_apps,
            "Exit": self.destroy,
        }

        self.package_table = PackageTable(
            self.list_frame, self.packages, output_callback=self.output_callback, actions=actions
        )
        self.package_table.grid(row=0, column=0, sticky=tk.NSEW)
        self.package_table.columnconfigure(0, weight=1)
        self.package_table.rowconfigure(0, weight=1)

        self.status_frame = ttk.Labelframe(p, text="Status", height=50)
        self.status_frame.columnconfigure(0, weight=1)
        self.status_frame.rowconfigure(0, weight=1)
        p.add(self.status_frame)

        self.info_text = ScrolledText(self.status_frame, height=10)
        self.info_text.grid(row=0, column=0, sticky=tk.NSEW)
        self.info_text.columnconfigure(0, weight=1)
        self.info_text.rowconfigure(0, weight=1)

        p.grid(row=0, column=0, sticky=tk.NSEW)
        p.columnconfigure(0, weight=1)
        p.rowconfigure(0, weight=1)

        ####################################################################################
        # status bar

        self.create_status_bar(row=1)
        self.set_status_bar_info("loading...")

        ####################################################################################

        # reconnect on startup:
        self.after(1, self.reconnect)
        self.mainloop()

    ###########################################################################
    # Status bar

    def create_status_bar(self, *, row):
        self.status_bar = MultiStatusBar(self)
        if sys.platform == "darwin":
            # Insert some padding to avoid obscuring some of the statusbar
            # by the resize widget.
            self.status_bar.set_label("_padding1", "    ", side=tk.RIGHT)
        self.status_bar.grid(row=row, column=0, sticky=tk.EW)

    def set_status_bar_info(self, text):
        self.status_bar.set_label(STATUSBAR_INFO_KEY, text)
        self.update_idletasks()

    def set_device_bar_info(self, text):
        self.status_bar.set_label(STATUSBAR_DEVICE_KEY, text)
        self.update_idletasks()

    ###########################################################################

    def output_callback(self, text, end="\n"):
        self.info_text.insert(tk.END, "%s%s" % (text, end))
        self.info_text.see(tk.END)
        self.update_idletasks()

    def stdout_redirect_handler(self, *args):
        # log.debug("redirect: %r", args)
        text = " ".join([str(part) for part in args])
        self.output_callback(text, end="")

    def subprocess(self, *args, timeout=10):
        info = " ".join(args)
        self.set_status_bar_info("%s..." % info)

        output = None
        try:
            with RedirectStdoutStderr(
                stdout_write=self.stdout_redirect_handler,
                stderr_write=self.stdout_redirect_handler, tee=True
            ):
                output = verbose_check_output(*args, timeout=timeout)
        except subprocess.CalledProcessError as err:
            print("ERROR: %s" % err)
            self.set_status_bar_info("%s - ERROR" % info)
        else:
            self.set_status_bar_info("%s - done" % info)
            print(output)  # print redirect output back to console ;)

        self.output_callback(text="", end="\n")

        return output

    def _uninstall(self, package_name):
        self.output_callback("_" * 80)
        self.output_callback("Uninstall app: %r" % package_name)
        self.subprocess("adb", "shell", "pm", "uninstall", "--user", "0", package_name, timeout=3)

    def _disable_user(self, package_name):
        self.output_callback("_" * 80)
        self.output_callback("Disable app: %r" % package_name)
        self.subprocess("adb", "shell", "pm", "disable-user", package_name, timeout=3)

    def _action(self, action_func):
        packages = self.packages.index2package.values()

        removed_packages = []
        for package in packages:
            if package.remove:
                removed_packages.append(package)
                action_func(package_name=package.package_name)

        if not removed_packages:
            messagebox.showinfo(title="Info", message="No packages selected !")

    def uninstall_apps(self):
        self._action(action_func=self._uninstall)

    def deactivate_apps(self):
        self._action(action_func=self._disable_user)

    def reconnect(self):
        """
        Kill adb server and reconnect device
        """
        self.output_callback("_" * 80)
        self.output_callback("Reconnect device...")
        self.subprocess("adb", "kill-server")
        self.subprocess("adb", "reconnect")

        self.list_devices()
        self.fetch_package_list()

    def list_devices(self):
        self.output_callback("_" * 80)
        self.output_callback("List devices via adb...")
        try:
            self.subprocess("adb", "wait-for-usb-device", timeout=5)
        except subprocess.TimeoutExpired as err:
            print("Error: %s" % err)
            print("Maybe 'USB Debugging' is not enabled on device?!?")

        output = self.subprocess("adb", "devices", "-l", timeout=3)
        # print(repr(output))
        self.output_callback(output)

        # example output e.g.:
        #
        # 'List of devices attached\nXYZ1234             device usb:3-10.4 product:foo model:bar device:foobar\n\n'

        if "attached" not in output:
            print("Output error :(")
            return

        lines = [line.strip() for line in output.splitlines() if line.strip()]

        # e.g.:
        # ['List of devices attached', 'XYZ1234             device usb:3-10.4 product:foo model:bar device:foobar']

        if len(lines) != 2:
            print("ERROR: Please connect only *one* device!")
            return

        devices_info = lines[1]
        devices_info = re.sub(r"\s{2,}", " - ", devices_info)

        # e.g.: "XYZ1234 - device usb:3-10.4 product:foo model:bar device:foobar"

        self.set_device_bar_info(devices_info)

    def fetch_package_list(self, *args):
        self.output_callback("_" * 80)
        self.output_callback("Fetch package list via adb...")

        packages = []
        output = self.subprocess("adb", "shell", "pm", "list", "packages", timeout=10)
        if not output:
            print("no process output")
            return

        for line in output.splitlines():
            if line.startswith("package:"):
                self.output_callback(".", end="")
                package_name = line[8:].strip()
                packages.append(package_name)

        self.output_callback("\n", end="")

        for no, package in enumerate(sorted(packages)):
            # self.output_callback(package)
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
