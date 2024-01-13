import sys

import gi

from gui.db_management_widget import DBManager

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class StartWindow(Gtk.ApplicationWindow):  # MainWindow
    def __init__(self, application):
        """ https://stackoverflow.com/questions/44509994/create-a-simple-tabbed-multi-page-application-with-python-and-gtk """
        super().__init__(application=application, title="WIP Podfic Poster")

        # TODO
        self.db_handler = None

        # Main grid
        self.main_grid = Gtk.Grid()
        self.main_grid.set_column_homogeneous(False)
        self.main_grid.set_row_homogeneous(True)
        self.add(self.main_grid)

        # Right panel for content
        right_content = Gtk.Stack()
        right_content.set_hexpand(True)
        right_content.set_vexpand(False)
        right_content.set_border_width(10)

        right_scrollable = Gtk.ScrolledWindow()
        right_scrollable.set_vexpand(True)
        right_scrollable.add(right_content)
        right_scrollable.set_propagate_natural_width(True)
        right_scrollable.set_propagate_natural_height(True)
        self.main_grid.attach(right_scrollable, 1, 0, 5, 1)

        # Left menu for navigation
        left_menu = Gtk.StackSidebar()
        left_menu.set_stack(right_content)
        self.main_grid.attach(left_menu, 0, 0, 1, 1)

        # DB Manager
        right_content.add_titled(DBManager(), "db_manager", "DB Manager")

        # Example of simple label content
        label = Gtk.Label(label="label 1 text inside")
        right_content.add_titled(label, "label_1_name", "label 1 menu title")

        self.show_all()




class PodficApplication(Gtk.Application):
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="org.example.myapp",
            **kwargs
        )
        self.main_window = None


    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.main_window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.main_window = StartWindow(application=self)

        self.main_window.present()


if __name__ == "__main__":
    app = PodficApplication()
    app.run(sys.argv)