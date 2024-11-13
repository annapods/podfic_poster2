from argparse import ArgumentError
from typing import Any, Callable, List, Literal, Optional, Tuple
import gi

from db.db_objects import Field, Record
# from gui.application import BaseApplication

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.overrides.Gtk import ScrolledWindow, ListStore, TreeView


type_mapping = {"TEXT": str, "INTEGER": int, "BOOLEAN": bool, "DATE":str}


class PaddedFrame(Gtk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = PaddedGrid()
        self.add(self.grid)


class PaddedGrid(Gtk.Grid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_row_spacing(5)
        self.set_border_width(5)
        self.set_column_homogeneous(True)
        self.set_row_homogeneous(True)
        self.last_added = None

    def attach_next(
            self, widget:Gtk.Widget, position=Gtk.PositionType.BOTTOM,
            width:int=1, height:int=1) -> None:
        if self.last_added is None:
            self.attach(widget, 0, 0, width, height)
            self.last_added = widget
        else:
            self.attach_next_to(widget, self.last_added, position, width, height)
            self.last_added = widget
    
    def attach(self, widget:Gtk.Widget, *args, **kwargs) -> None:
        super().attach(widget, *args, **kwargs)
        self.last_added = widget
    
    def attach_next_to(self, widget:Gtk.Widget, *args, **kwargs) -> None:
        super().attach_next_to(widget, *args, **kwargs)
        self.last_added = widget


class TableGrid(PaddedGrid):
    """ Table that can show data from records
    Columns can be set at init or be calculated dynamically from the records given """

    def __init__(
            self, label:str, selection_mode:str, on_selection_changed:Callable,
            set_fields:Optional[List[Field]]=[], include_display_name:Optional[bool]=False,
            override_not_display_fields:Optional[bool]=False,
            *args, **kwargs):
        """ To dynamically refresh columns based on records, leave set_fields out """

        super().__init__(*args, **kwargs)
        self._set_fields = set_fields != []
        self._include_display_name = include_display_name
        self._override_not_display_fields = override_not_display_fields
        self._column_names = []
        self._column_types = []
        self._recalculate_columns(set_fields)

        # ListStore model
        self._datastore = Gtk.ListStore(*self._column_types)
        # Treeview, making it use the filter as a model, and adding the columns
        self._treeview = Gtk.TreeView()
        self._reset_treeview()
        # Selection method
        if selection_mode:
            tree_selection = self._treeview.get_selection()
            if selection_mode == "single":
                tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
            elif selection_mode == "multiple":
                tree_selection.set_mode(Gtk.SelectionMode.MULTIPLE)
            else:
                raise(ArgumentError(message="BUG found: selection_mode must be single or multiple"))
            tree_selection.connect("changed", on_selection_changed)

        # Put the treeview in a scrollwindow
        self._widget = Gtk.ScrolledWindow()
        self._widget.set_vexpand(True)
        self._widget.add(self._treeview)
        # And the scrollwindow in a frame
        self._frame = PaddedFrame(label=label)
        self._frame.grid.attach_next(
            self._widget, width=10, height=3)
        self.attach_next(self._frame, Gtk.PositionType.BOTTOM, 10, 3)

    def _reset_datastore(self, data:List[Optional[List[Any]]]):
        """ Reset the table data """
        self._datastore.clear()
        for line in data:
            if line: self._datastore.append(list(line))

    def _reset_treeview(self):
        """ Reset the table columns """
        # Model
        self._treeview.set_model(self._datastore)
        # Remove columns
        for column_name in self._treeview.get_columns():
            self._treeview.remove_column(column_name)
        # Reformat, underscores get skipped otherwise
        columns = [c.replace("_", " ").upper() for c in self._column_names]
        # (Re)add columns
        for i, column_name in enumerate(columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_name, renderer, text=i)
            column.set_expand(True)
            column.set_resizable(True)
            self._treeview.append_column(column)

    def _recalculate_columns(self, fields:Optional[List[Field]]=[]):
        """ Recalculate column names and types based on given fields and init display parameters """
        self._column_names = ["display_name"] if self._include_display_name else []
        self._column_types = [str] if self._include_display_name else []

        for field in fields:
            if field.display_in_table or self._override_not_display_fields:
                self._column_names.append(field.field_name)
                self._column_types.append(type_mapping[field.type])

    def reload_table(
            self, records:Optional[List[Record]]
            ) -> None:
        """ Reload the table with the given records
        Warning, might not display columns if there is no record and no set columns were specified for this table """

        data = []
        
        if records:
            # Double check that all records are in the same table
            parent_table = records[0].parent_table
            for r in records:
                assert r.parent_table == parent_table

            # If no set columns at init, recalculate them based on given records
            if not self._set_fields:
                self._recalculate_columns(records[0].parent_table.fields)

            # Get values
            for record in records:
                data.append([record.values[f] for f in record.values.keys() if f.field_name in self._column_names])
                # Note: value keys are Field objects, not their str names

        # Reinitiate table with new columns (if applicable) and data
        if not self._set_fields: self._datastore = Gtk.ListStore(*self._column_types)
        self._reset_datastore(data)
        self._reset_treeview()


