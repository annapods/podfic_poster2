from typing import Any, Callable, List, Optional
from gi.repository.Gtk import ListStore, TreeView, TreeSelection, PositionType, CellRendererText, TreeViewColumn, SelectionMode


from db.objects import Field, Record, Table, TextField, IntField, BoolField, DateField, FilepathField, LengthField
from gui.base_graphics import PaddedFrame, PaddedGrid, ScrollWindow


py_to_gtk_type_mapping = {
    TextField: str,
    IntField: int,
    BoolField: bool,
    DateField: str,
    FilepathField: str,
    LengthField: str
}


class TableWidget(PaddedGrid):
    """ Table that can show data from records
    Columns can be set at init or be calculated dynamically from the records given
    Selection is implemented at subclass level
    External interface:
    - self.current_selection, Record or list of Records
    - self.load_options(records:Optional[List[Record]])
    - self.set_selected(to_select:Record|int)
    Calls on_change_notify (init arg) when the selection changes """

    def __init__(
            self, on_change_notify:Callable,
            set_fields:Optional[List[Field]]=[],
            *args, **kwargs):
        """ To dynamically refresh columns based on records, leave fields out """

        super().__init__(*args, **kwargs)
        self._set_fields = set_fields != []
        self.current_selection = None
        self._records = []

        # Fields and columns
        self._treeview = TreeView()
        self._reset_fields(set_fields)

        # Selection method
        self._tree_selection = self._treeview.get_selection()
        self._set_selection_mode()
        
        # Fetch current ID(s) on selection changed
        def _on_selection_changed(selection:TreeSelection):
            self._fetch_current(selection)
            on_change_notify()
        
        self._tree_selection.connect("changed", _on_selection_changed)

        self._widget = ScrollWindow()
        self._widget.add(self._treeview)
        self.attach_next(self._widget, PositionType.BOTTOM)

    def _reset_fields(self, fields):
        """ Reset the columns/fields of the table """
        self._fields = fields
        self._table = None if fields == [] else fields[0].parent_table

        # Double check fields, sort, add ID at the start if needed
        if self._fields != []:
            for f in self._fields: assert f.parent_table == self._table
            self._fields.sort(key=lambda f: f.display_order)
            id_field = self._table.get_field("ID")
            if self._fields[0] != id_field:
                self._fields.remove(id_field)
                self._fields = [id_field]+self._fields
        
        # Reset datastore
        self._datastore = ListStore(*[py_to_gtk_type_mapping[type(f)] for f in self._fields])
        # Reset treeview model and columns
        self._treeview.set_model(self._datastore)
        for column_name in self._treeview.get_columns():
            self._treeview.remove_column(column_name)
        # Reformat, underscores get skipped otherwise
        columns = [f.field_name.replace("_", " ").upper() for f in self._fields]
        # (Re)add columns
        for i, column_name in enumerate(columns):
            renderer = CellRendererText()
            column = TreeViewColumn(column_name, renderer, text=i)
            column.set_expand(True)
            column.set_resizable(True)
            self._treeview.append_column(column)

    def _set_selection_mode(self):
        raise NotImplementedError
    
    def _fetch_current(self, selection:TreeSelection):
        raise NotImplementedError

    def _find_record_by_ID(self, to_find:int) -> Record|None:
        if self._records:
            for record in self._records:
                if record.ID == to_find:
                    return record
        self._vprint("DEBUG", f"Record ID {to_find} cannot be found here.")
        return None

    def _find_row_number_by_ID(self, to_find) -> Record|None:
        i = None
        if self._records:
            for i, record in enumerate(self._records):
                if record.ID == to_find:
                    return i
        self._vprint("DEBUG", f"Record ID {to_find} cannot be found here.")
        return None

    def load_options(self, records:Optional[List[Record]]) -> None:
        """ Reload the table with the given records
        Warning, might not display columns if there is no record and no set columns were specified for this table """

        self._datastore.clear()

        if records:
            # If no set columns at init, recalculate them based on given records
            # The data table is also dynamic in that case
            if not self._set_fields: self._reset_fields(records[0].parent_table.fields)
            # Double check that all records are in the same table
            for r in records: assert r.parent_table == self._table
            # Sort records
            records.sort(key=lambda r: r.values[self._table.sort_rows_by])
            self._records = records
        
            for record in records:
                try:
                    self._datastore.append([record.values[f] for f in self._fields])
                except Exception as e:
                    self._vprint(f"DEBUG couldn't add record to table widget...\nTable:{self._table}\nFields:{self._fields}\nRecord: {record}")
                    raise e

    def set_selected(self, to_select:Record|int|None) -> None:
        if to_select is None:
            self._treeview.get_selection().unselect_all()
            return
        elif type(to_select) is Record:
            to_select = to_select.ID
        row_number = self._find_row_number_by_ID(to_select)
        if not row_number is None:
            self._treeview.set_cursor(self._find_row_number_by_ID(to_select))
        else:
            self._treeview.get_selection().unselect_all()


class SingleSelectTable(TableWidget):
    def _set_selection_mode(self):
        self._tree_selection.set_mode(SelectionMode.SINGLE)
    def _fetch_current(self, selection) -> Record:
        (model, pathlist) = selection.get_selected_rows()
        self.current_selection = None
        for path in pathlist:
            record_id =  model.get_value(model.get_iter(path), 0)
            self.current_selection = self._find_record_by_ID(record_id)

class MultiSelectTable(TableWidget):
    def _set_selection_mode(self):
        self._tree_selection.set_mode(SelectionMode.MULTIPLE)
    def _fetch_current(self, selection) -> List[Record]:
        (model, pathlist) = selection.get_selected_rows()
        self.current_selection = []
        for path in pathlist:
            record_id =  model.get_value(model.get_iter(path), 0)
            self.current_selection.append(self._find_record_by_ID(record_id))

