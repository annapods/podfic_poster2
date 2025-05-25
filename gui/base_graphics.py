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

class PlainGrid(Grid, BaseObject):  # TODO cannot add verbose mode...
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._verbose = True  #DEBUG need to check why I need to declare it here...
        self.set_row_spacing(5)
        self.set_column_spacing(5)
        self.set_column_homogeneous(False)
        self.set_row_homogeneous(False)
        # Required for scroll windows to go to the edges of the window
        # instead of just min size of scroll and/or max height of contents
        self.set_hexpand(True)
        self.set_vexpand(True)
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
    
    def attach(
            self, widget:Widget, left:int=1, top:int=1,
            width:int=1, height:int=1) -> None:
        Grid.attach(self, widget, left, top, width, height)
        self.last_added = widget
    
    def attach_next_to(
            self, widget:Widget, next_to:Widget, position=PositionType.BOTTOM,
            width:int=1, height:int=1) -> None:
        Grid.attach_next_to(self, widget, next_to, position, width, height)
        self.last_added = widget


class PaddedGrid(PlainGrid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_border_width(5)


class ScrollWindow(ScrolledWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # DEBUG size
        # min content is the only way so far to set up the size of a scroll window
        self.set_min_content_height(150)
        # self.set_max_content_height(500)
        self.set_min_content_width(300)
        # self.set_max_content_width(500)
        # Make widget expand if window size gets bigger
        # self.set_vexpand(True)
        # self.set_hexpand(True)
        # Attempt to tell parents to fit the size of the children
        # self.set_propagate_natural_width(True)
        self.set_propagate_natural_height(True)
