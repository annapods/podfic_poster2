from typing import Any, Callable, List, Optional
from gi.repository.Gtk import ListStore, TreeView, TreeSelection, PositionType, CellRendererText, TreeViewColumn, SelectionMode


from db.objects import Field, Record, TextField, IntField, BoolField, DateField, FilepathField, LengthField
from gui.base_graphics import PaddedFrame, PaddedGrid, ScrollWindow


py_to_gtk_type_mapping = {
    TextField: str,
    IntField: int,
    BoolField: bool,
    DateField: str,
    FilepathField: str,
    LengthField: str
}


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
        self._datastore = ListStore(*self._column_types)
        # Treeview, making it use the filter as a model, and adding the columns
        self._treeview = TreeView()
        self._reset_treeview()

        # Selection method and to do on select
        self._tree_selection = self._treeview.get_selection()
        self._set_selection_mode()
        
        def _on_selection_changed(selection:TreeSelection):
            self._fetch_current(selection)
            do_after_select()
        
        self._tree_selection.connect("changed", _on_selection_changed)


        # Put the treeview in a scrollwindow
        self._widget = ScrollWindow()
        self._widget.add(self._treeview)
        # And the scrollwindow in a frame
        self._frame = PaddedFrame(label=label)
        self._frame.grid.attach_next(self._widget)
        self.attach_next(self._frame, PositionType.BOTTOM)

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
            renderer = CellRendererText()
            column = TreeViewColumn(column_name, renderer, text=i)
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
                self._column_types.append(py_to_gtk_type_mapping[type(field)])

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
        if not self._set_fields: self._datastore = ListStore(*self._column_types)
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
        self._tree_selection.set_mode(SelectionMode.SINGLE)
    def _fetch_current(self, selection):
        (model, pathlist) = selection.get_selected_rows()
        self.current_selection = None
        for path in pathlist:
            tree_iter = model.get_iter(path)
            self.current_selection = model.get_value(tree_iter, 0)

class MultiSelectTable(TableGrid):
    def _set_selection_mode(self):
        self._tree_selection.set_mode(SelectionMode.MULTIPLE)
    def _fetch_current(self, selection):
        (model, pathlist) = selection.get_selected_rows()
        self.current_selection = []
        for path in pathlist :
            tree_iter = model.get_iter(path)
            current_id = model.get_value(tree_iter, 1)
            self.current_selection.append(current_id)
