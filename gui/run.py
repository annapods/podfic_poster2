from sys import argv
import gi
gi.require_version("Gtk", "3.0")

from gui.workflows.error_handler import setup_popup_logger
from gui.workflows.application import PodficApplication

if __name__ == "__main__":
    setup_popup_logger()
    app = PodficApplication()
    app.run(argv)
