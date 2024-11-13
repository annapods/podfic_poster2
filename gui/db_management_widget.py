from typing import Any, List, Optional
from db.db_objects import Record, Table
from gui.base_graphics import PaddedFrame, PaddedGrid, TableGrid
from gi.repository import Gtk
from db.db_handler import SQLiteHandler
from gi.overrides.Gtk import TreeSelection, Button

from gui.db_record_widget import RecordManager



class DBManager(PaddedGrid):

    def __init__(self):
        super().__init__()

        self.db_path = ""
        self.db_path = "db/podfics.db"  # for quicker debugging
        self.db_handler = None
        self.current_table = None
        self.current_fields = []
        self.current_record = None
        
        # Database picker
        self._db_picker = Gtk.FileChooserButton(
            title="Select the database", action=Gtk.FileChooserAction.OPEN)
        self._db_picker.set_current_folder('./db')
        self._db_picker.connect("file-set", self._on_file_picked)
        database_frame = PaddedFrame(label="Database")
        database_frame.grid.attach_next(self._db_picker, width=10)
        self.attach(database_frame, 0, 0, 10, 1)

        # Reload database button
        reload_button = Gtk.Button(label="Reload")
        reload_button.connect("clicked", self.on_button_reload_clicked)
        database_frame.grid.attach_next(reload_button, Gtk.PositionType.RIGHT)

        # Tables
        self._table_frame = TableGrid("Tables", "single", self._on_table_selection_changed)
        self.attach_next(self._table_frame, Gtk.PositionType.BOTTOM, 10, 3)
        self._field_frame = TableGrid("Table fields", "multiple", self._on_fields_selection_changed)
        self.attach_next(self._field_frame, Gtk.PositionType.BOTTOM, 10, 3)
        self._record_frame = TableGrid("Table records", "single", self._on_records_selection_changed)
        self.attach_next(self._record_frame, Gtk.PositionType.BOTTOM, 10, 3)

        # Record buttons
        self._record_buttons = {}
        record_buttons_grid = PaddedGrid()
        for i, (key, label, on_button_clicked) in enumerate([
                ("delete", "Delete", self.on_button_delete_clicked)
            ]):
            self._record_buttons[key] = Gtk.Button(label=label)
            self._record_buttons[key].connect("clicked", on_button_clicked)
            if i == 0:
                record_buttons_grid.attach(self._record_buttons[key], 0,0,1,1)
            else:
                record_buttons_grid.attach_next(
                    self._record_buttons[key],
                    Gtk.PositionType.RIGHT, 1, 1)
        self._record_frame._frame.grid.attach_next(
            record_buttons_grid, Gtk.PositionType.BOTTOM, 3, 1)

        # Record form
        self._record_grid = RecordManager(self.db_handler)
        record_frame = PaddedFrame(label="Record form")
        # swap default grid for RecordManager
        record_frame.remove(record_frame.grid)
        record_frame.grid = self._record_grid
        record_frame.add(record_frame.grid)
        self.attach_next(
            record_frame, Gtk.PositionType.BOTTOM, 10, 3)
        
        
    def load_values(
            self, current_table:Optional[Table]=None,
            current_record:Optional[Record]=None
        ) -> None:
        """ Refresh the page with the given selection, if applicable """
        self.current_table = current_table
        self._reload_tables_table()
        self._reload_fields_table()
        self._reload_records_table()
        self.current_record = current_record
        self._reload_record_form()
    

    def _reload_tables_table(self) -> None:
        """ Reload the tables table
        This table shows the data_table records """
        records = self.db_handler.get_records(table="data_table")
        self._table_frame.reload_table(records)
        self.current_fields = []
    
    def _reload_fields_table(self) -> None:
        """ Reload the fields table for the current table selected, if any
        This table shows the data_field records with a filter on the data_table if applicable"""
        records = self.db_handler.get_records(
            table="data_field",
            where_condition=f'''table_name="{self.current_table.table_name}"''' if self.current_table else ""
        )
        self._field_frame.reload_table(records)

    def _reload_records_table(self) -> None:
        """ Reload the records table
        This table shows the records of the selected table, if any
        If no table has been selected, or if the table is empty, nothing will be shown, not even column headers """
        if self.current_table:
            records = \
                self.db_handler.get_records(
                    table=self.current_table, sort_by=None
            )
        else:
            records = []
        self._record_frame.reload_table(records)


    def _reload_db(self) -> None:
        """ """
        self.db_handler = SQLiteHandler(self.db_path)
        self._record_grid.db_handler = self.db_handler
        self.load_values(None, None)
    
    def _reload_record_form(self) -> None:
        """ """
        if self.current_record and self.current_table:
            self._record_grid.init_form_from_record(self.current_record)
        elif self.current_table:
            self._record_grid.init_form_from_table(self.current_table)
        else: pass
            

    def _on_file_picked(self, file_chooser_button):
        """ Callback for database file selection """
        self.db_path = file_chooser_button.get_filename()
        self._reload_db()


    def _on_table_selection_changed(self, selection:TreeSelection) -> None:
        """ Callback for table selection """
        (model, pathlist) = selection.get_selected_rows()
        for path in pathlist :
            tree_iter = model.get_iter(path)
            current_id = model.get_value(tree_iter, 0)
            self.current_table = self.db_handler.data_model.get_table(current_id)
        self.current_fields = []
        self._reload_fields_table()
        self._reload_record_form()

    def _on_fields_selection_changed(self, selection:TreeSelection) -> None:
        """ Callback for fields selection """
        (model, pathlist) = selection.get_selected_rows()
        self.current_fields = []
        for path in pathlist :
            tree_iter = model.get_iter(path)
            current_id = model.get_value(tree_iter, 1)
            self.current_fields.append(current_id)
        self._reload_records_table()
    
    def _on_records_selection_changed(self, selection:TreeSelection) -> None:
        """ Callback for record selection """
        (model, pathlist) = selection.get_selected_rows()
        for path in pathlist :
            tree_iter = model.get_iter(path)
            current_id = model.get_value(tree_iter, 0)
            self.current_record = self.db_handler.get_record(table=self.current_table, display_name=current_id)
        self._reload_record_form()
        


    def on_button_reload_clicked(self, button:Button) -> None:
        """ """
        self._reload_db()

    def on_button_delete_clicked(self, button:Button) -> None:
        """ """
        # TODO confirmation popup
        pass
