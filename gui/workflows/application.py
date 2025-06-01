from gi.repository.Gtk import ApplicationWindow, Grid, Stack, StackSidebar, Label, Application

from gui.bricks.containers import ScrollWindow
from gui.workflows.db_manager import DBManager2


class MainWindow(ApplicationWindow):
    """ Main window of the application, navigation level
    Contains a menu to the left that selects the content of the panel to the left
    https://stackoverflow.com/questions/44509994/create-a-simple-tabbed-multi-page-application-with-python-and-gtk """

    def __init__(self, application):
        """ """
        super().__init__(application=application, title="WIP Podfic Poster")

        # Only affects the overall window, as if the user had resized it
        self.set_default_size(800,750)  #DEBUG size

        # TODO for now, the only DBHandler is in the db_management_widget level
        # this allows for easily switching DB files, but we're going to need db functionalities in other modules too
        self.db_handler = None

        # Main grid, will only contain right content panel and left navigation sidebar
        self.main_grid = Grid()
        # self.main_grid.set_column_homogeneous(False)
        self.add(self.main_grid)

        # Right panel for content, will be filled dynamically by the options of the left navifation sidebar
        right_content = Stack()
        right_content.set_border_width(10)
        # Scrollable vertically
        right_scrollable = ScrollWindow()
        right_scrollable.add(right_content)
        self.main_grid.attach(right_scrollable, 1, 0, 1, 1)  # right, top, width, height

        # Left menu for navigation
        left_menu = StackSidebar()
        left_menu.set_stack(right_content)
        self.main_grid.attach(left_menu, 0, 0, 1, 1)

        # DB Manager
        self.db_manager = DBManager2()
        self.db_manager.tests()  # TEST
        right_content.add_titled(self.db_manager, "db_manager", "DB Manager")

        # # Example of simple label content
        # content = Gtk.Label(label="this text shows in the right panel")
        # right_content.add_titled(content, "label_1_name", "menu title")

        # Project main view, for later
        placeholder = Label(label="TODO")
        right_content.add_titled(placeholder, "projects", "Projects")

        # Application parameters, for later
        placeholder = Label(label="Settings:\n"+\
            "add self as person, add own socmed accounts\n"+\
            "add default database for projects\n"+\
            "add secrets?\n"+\
            "guided set up if possible")
        right_content.add_titled(placeholder, "settings", "Settings")

        self.show_all()




class PodficApplication(Application):
    """ Application, highest level """
    
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="org.example.myapp",
            **kwargs
        )
        self.main_window = None


    def do_startup(self):
        Application.do_startup(self)

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.main_window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.main_window = MainWindow(application=self)

        self.main_window.present()

