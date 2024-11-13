import sys

import gi

from gui.db_management_widget import DBManager

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class StartWindow(Gtk.ApplicationWindow):
    """ Main window of the application, navigation level
    Contains a menu to the left that selects the content of the panel to the left
    https://stackoverflow.com/questions/44509994/create-a-simple-tabbed-multi-page-application-with-python-and-gtk """

    def __init__(self, application):
        """ """
        super().__init__(application=application, title="WIP Podfic Poster")

        # TODO for now, the only DBHandler is in the db_management_widget level
        # this allows for easily switching DB files, but we're going to need db functionalities in other modules too
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

        # # Example of simple label content
        # content = Gtk.Label(label="this text shows in the right panel")
        # right_content.add_titled(content, "label_1_name", "menu title")

        # Project main view, for later
        placeholder = Gtk.Label(label="TODO")
        right_content.add_titled(placeholder, "projects", "Projects")

        # Application parameters, for later
        placeholder = Gtk.Label(label="TODO")
        right_content.add_titled(placeholder, "settings", "Settings")

        self.show_all()




class PodficApplication(Gtk.Application):
    """ Application, highest level """
    
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