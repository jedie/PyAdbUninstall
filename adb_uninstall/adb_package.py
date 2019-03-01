import logging
import subprocess
import webbrowser

from adb_uninstall.constants import GOOGLE_PLAY_URL, LOCKED_APPS
from adb_uninstall.subprocess2 import iter_subprocess_output

log = logging.getLogger(__name__)


class Package:
    KEEP = "keep"
    REMOVE = "remove"
    LOCKED = "locked"

    def __init__(self, *, package_name, index, action=None):
        self.package_name = package_name
        self.index = index

        if package_name in LOCKED_APPS:
            self.action = self.LOCKED
        elif action is None:
            self.action = self.KEEP
        else:
            assert action in (self.KEEP, self.REMOVE)
            self.action = action

    @property
    def locked(self):
        return self.action == self.LOCKED

    @property
    def keep(self):
        return self.action == self.KEEP

    @property
    def remove(self):
        return self.action == self.REMOVE

    def set_keep(self):
        self.action = self.KEEP

    def set_remove(self):
        if self.action == self.LOCKED:
            raise AssertionError("Can't remove locked app!")

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

        return package

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
