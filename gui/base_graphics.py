from argparse import ArgumentError
from typing import Any, Callable, List, Literal, Optional, Tuple
import gi

from src.base_object import BaseObject
from db.db_objects import Field, Record
# from gui.application import BaseApplication

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.overrides.Gtk import ScrolledWindow, ListStore, TreeView, TreeSelection


type_mapping = {"TEXT": str, "INTEGER": int, "BOOLEAN": bool, "DATE":str}


class PaddedFrame(Gtk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = PaddedGrid()
        self.add(self.grid)


class PaddedGrid(Gtk.Grid, BaseObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self._verbose = True  # DEBUG need to check why I need to declare it here...
        self.set_row_spacing(5)
        self.set_border_width(5)
        self.set_column_homogeneous(True)
        self.set_row_homogeneous(False)
        self.set_hexpand(True)
        self.set_vexpand(False)
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
    Columns can be set at init or be calculated dynamically from the records given
    Selection is implemented at subclass level """

    def __init__(
            self, label:str, do_after_select:Callable,
            set_fields:Optional[List[Field]]=[], include_technical_columns:Optional[bool]=False,
            *args, **kwargs):
        """ To dynamically refresh columns based on records, leave set_fields out """

        super().__init__(*args, **kwargs)
        self._set_fields = set_fields != []
        self._include_technical_columns = include_technical_columns
        self._column_names = []
        self._column_types = []
        self._recalculate_columns(set_fields)
        self.current_selection = None

        # ListStore model
        self._datastore = Gtk.ListStore(*self._column_types)
        # Treeview, making it use the filter as a model, and adding the columns
        self._treeview = Gtk.TreeView()
        self._reset_treeview()

        # Selection method and to do on select
        self._tree_selection = self._treeview.get_selection()
        self._set_selection_mode()
        
        def _on_selection_changed(selection:TreeSelection):
            self._fetch_current(selection)
            do_after_select()
        
        self._tree_selection.connect("changed", _on_selection_changed)


        # Put the treeview in a scrollwindow
        self._widget = get_scroll_window()
        self._widget.add(self._treeview)
        # And the scrollwindow in a frame
        self._frame = PaddedFrame(label=label)
        self._frame.grid.attach_next(self._widget)
        self.attach_next(self._frame, Gtk.PositionType.BOTTOM)

    def _set_selection_mode(self):
        raise NotImplementedError
    
    def _fetch_current(self, selection:TreeSelection):
        raise NotImplementedError

    
    def _reset_datastore(self, data:List[Optional[List[Any]]]):
        """ Reset the table data """
        self._datastore.clear()
        for line in data:
            try:
                if line: self._datastore.append(list(line))
            except Exception as e:
                self._vprint(f"DEBUG couldn't add line to table {line}")
                raise e

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
        self._column_names = []
        self._column_types = []
        for field in fields:
            if self._include_technical_columns or field.field_name not in ["display_name", "ID", "creation_date"]:
                self._column_names.append(field.field_name)
                self._column_types.append(type_mapping[field.type])

    def reload_table(self, records:Optional[List[Record]]) -> None:
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
                # Note: value keys are Field objects, not their str field_names
                record_data = [record.values[f] for f in record.values.keys() if f.field_name in self._column_names]
                if self._include_technical_columns: record_data = [record.ID, record.display_name] + record_data
                data.append(record_data)
        
        # Reinitiate table with new columns (if applicable) and data
        if not self._set_fields: self._datastore = Gtk.ListStore(*self._column_types)
        try:
            self._reset_datastore(data)
        except Exception as e:
            self._vprint(f"DEBUG table {records[0].parent_table.table_name}")
            self._vprint(f"DEBUG columns {self._column_names}")
        self._reset_treeview()

    def set_selected(self, to_select):
        if to_select is None: self._treeview.get_selection().unselect_all()
        else: self._treeview.set_cursor(to_select)  # DEBUG haven't tested this part


class SingleSelectTable(TableGrid):
    def _set_selection_mode(self):
        self._tree_selection.set_mode(Gtk.SelectionMode.SINGLE)
    def _fetch_current(self, selection):
        (model, pathlist) = selection.get_selected_rows()
        self.current_selection = None
        for path in pathlist:
            tree_iter = model.get_iter(path)
            self.current_selection = model.get_value(tree_iter, 0)

class MultiSelectTable(TableGrid):
    def _set_selection_mode(self):
        self._tree_selection.set_mode(Gtk.SelectionMode.MULTIPLE)
    def _fetch_current(self, selection):
        (model, pathlist) = selection.get_selected_rows()
        self.current_selection = []
        for path in pathlist :
            tree_iter = model.get_iter(path)
            current_id = model.get_value(tree_iter, 1)
            self.current_selection.append(current_id)


def get_scroll_window():
        # Put the treeview in a scrollwindow
        widget = Gtk.ScrolledWindow()
        widget.set_min_content_height(150)
        widget.set_max_content_height(300)
        widget.set_max_content_width(300)
        # Make widget expand if window size gets bigger
        widget.set_vexpand(True)
        widget.set_hexpand(True)
        widget.set_propagate_natural_width(False)
        widget.set_propagate_natural_height(True)
        return widget