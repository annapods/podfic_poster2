from argparse import ArgumentError
from typing import Any, List, Literal, Optional, Tuple
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.overrides.Gtk import ScrolledWindow, ListStore, TreeView



# def get_datastore(column_types:List[type]) -> ListStore:
#     return Gtk.ListStore(*column_types)

def init_datastore(
        datastore:ListStore, data:List[Optional[List[Any]]]
        ) -> ListStore:
    datastore.clear()
    for record in data:
        if record: datastore.append(list(record))
    return datastore

def init_treeview(
        treeview, model:ListStore, column_names:List[str],
        selection_mode:Optional[Literal["single", "multiple"]] = None,
        on_selection_changed:Optional[callable] = None
        ) -> TreeView:
    
    # Model
    treeview.set_model(model)
    
    # Columns
    for column_name in treeview.get_columns():
        treeview.remove_column(column_name)
    for i, column_name in enumerate(column_names):
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(column_name, renderer, text=i)
        column.set_expand(True)
        column.set_resizable(True)
        treeview.append_column(column)

    # Selection
    if selection_mode:
        tree_selection = treeview.get_selection()
        if selection_mode == "single":
            tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
        elif selection_mode == "multiple":
            tree_selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        else:
            raise(ArgumentError(message="BUG found: selection_mode must be single or multiple"))
        tree_selection.connect("changed", on_selection_changed)

    return treeview

def init_scrolled_table(scrolled_window:ScrolledWindow, treeview:TreeView) -> ScrolledWindow:
    scrolled_window.set_vexpand(True)
    scrolled_window.add(treeview)
    return scrolled_window


def generate_table(
        column_names:List[str], column_types:List[type], data:List[List[Any]],
        selection_mode:Optional[Literal["single", "multiple"]] = None,
        on_selection_changed:Optional[callable] = None
        ) -> Tuple[ScrolledWindow, ListStore]:
    """ Generate a scrollable window, treelist and datastore according to the given parameters """

    # Creating the ListStore model
    datastore = Gtk.ListStore(*column_types)
    datastore = init_datastore(datastore, data)

    # creating the treeview, making it use the filter as a model, and adding the columns
    treeview = Gtk.TreeView()
    treeview = init_treeview(treeview, datastore, column_names, selection_mode, on_selection_changed)

    # putting the treeview in a scrollwindow
    widget = Gtk.ScrolledWindow()
    widget = init_scrolled_table(widget, treeview)

    return widget, treeview, datastore
        

class BaseWindow(Gtk.Window):

    def __init__(self, title:str):
        super().__init__(title=title)
        self.set_border_width(10)

        # Setting up the self.grid in which the elements are to be positioned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.add(self.grid)

