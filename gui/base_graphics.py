import gi
gi.require_version("Gtk", "3.0")
from gi.repository.Gtk import Grid, Frame, Widget, PositionType, ScrolledWindow


from src.base_object import BaseObject
from db.objects import Field, Record
# from gui.application import BaseApplication


class PaddedFrame(Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = PaddedGrid()
        self.add(self.grid)


class PaddedGrid(Grid, BaseObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._verbose = True  # DEBUG need to check why I need to declare it here...
        self.set_row_spacing(5)
        self.set_column_spacing(5)
        self.set_border_width(5)
        self.set_column_homogeneous(True)
        self.set_row_homogeneous(False)
        self.set_hexpand(True)
        self.set_vexpand(False)
        self.last_added = None

    def attach_next(
            self, widget:Widget, position=PositionType.BOTTOM,
            width:int=1, height:int=1) -> None:
        if self.last_added is None:
            self.attach(widget, 0, 0, width, height)
            self.last_added = widget
        else:
            self.attach_next_to(widget, self.last_added, position, width, height)
            self.last_added = widget
    
    def attach(self, widget:Widget, *args, **kwargs) -> None:
        super().attach(widget, *args, **kwargs)
        self.last_added = widget
    
    def attach_next_to(self, widget:Widget, *args, **kwargs) -> None:
        super().attach_next_to(widget, *args, **kwargs)
        self.last_added = widget


class ScrollWindow(ScrolledWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_min_content_height(150)
        self.set_max_content_height(300)
        self.set_max_content_width(300)
        # Make widget expand if window size gets bigger
        self.set_vexpand(True)
        self.set_hexpand(True)
        self.set_propagate_natural_width(False)
        self.set_propagate_natural_height(True)
