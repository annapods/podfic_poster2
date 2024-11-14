from typing import Any, List, Optional
from db.db_objects import Record, Table
from gui.base_graphics import MultiSelectTable, PaddedFrame, PaddedGrid, SingleSelectTable, TableGrid
from gi.repository import Gtk
from db.db_handler import SQLiteHandler
from gi.overrides.Gtk import Button

from gui.db_record_widget import RecordManager



class DBManager(PaddedGrid):

    def __init__(self):
        super().__init__()

        # Current selections and helpers
        self.database_path = ""
        self.db_handler = None
        self.current_table = None
        self.current_fields = []  # Obsolete, was intended to filter the columns to show in records table
        self.current_record = None
        
        # Database picker
        db_picker = Gtk.FileChooserButton(
            title="Select the database", action=Gtk.FileChooserAction.OPEN)
        db_picker.set_current_folder('./db')
        db_picker.connect("file-set", self._on_file_picked)

        # Reload database button
        reload_button = Gtk.Button(label="Reload")
        reload_button.connect("clicked", self.on_button_reload_clicked)
        reload_button.vexpand = False

        # Database picker and button in a single frame
        database_frame = PaddedFrame(label="Database")
        database_frame.grid.attach_next(db_picker)
        database_frame.grid.attach_next(reload_button, Gtk.PositionType.RIGHT)
        self.attach_next(database_frame)

        # Tables
        self._tables_table = SingleSelectTable("Tables", self._on_table_selection_changed)
        self.attach_next(self._tables_table)
        self._fields_table = MultiSelectTable("Table fields", self._on_fields_selection_changed)
        self.attach_next(self._fields_table)
        self._records_table = SingleSelectTable("Table records", self._on_records_selection_changed)
        self.attach_next(self._records_table)

        # Record form
        self._record_grid = RecordManager(self.db_handler)
        record_frame = PaddedFrame(label="Record form")
        # swap default grid for RecordManager
        record_frame.remove(record_frame.grid)
        record_frame.grid = self._record_grid
        record_frame.add(record_frame.grid)
        self.attach_next(
            record_frame, Gtk.PositionType.BOTTOM)  #, 10, 3)
    

    def _reload_db(self) -> None:
        """ """
        self.db_handler = SQLiteHandler(self.database_path)
        self.db_handler.change_db(self.database_path)
        self._record_grid.db_handler = self.db_handler
        self._reload_tables_table()

    def _reload_tables_table(self) -> None:
        """ Reload the tables table
        This table shows the data_table records """
        records = self.db_handler.get_records(table="data_table")
        self._tables_table.reload_table(records)
        self.current_fields = None
        self._reload_fields_table()
        self._reload_records_table()
    
    def _reload_fields_table(self) -> None:
        """ Reload the fields table for the current table selected, if any
        This table shows the data_field records with a filter on the data_table if applicable"""
        records = self.db_handler.get_records(
            table="data_field",
            where_condition=f'''table_name="{self.current_table.table_name}"''' if self.current_table else ""
        )
        self._fields_table.reload_table(records)

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
        self._records_table.reload_table(records)
        self.current_record = None
        self._reload_record_form()


    def _reload_record_form(self) -> None:
        """ """
        if self.current_record and self.current_table:
            self._record_grid.init_form_from_record(self.current_record)
        elif self.current_table:
            self._record_grid.init_form_from_table(self.current_table)
        else:
            self._record_grid.init_form_from_nothing()
            

    def _on_file_picked(self, file_chooser_button):
        """ Callback for database file selection """
        self.database_path = file_chooser_button.get_filename()
        self._tables_table.set_selected(None)
        self._fields_table.set_selected(None)
        self._records_table.set_selected(None)
        self._reload_db()


    def _on_table_selection_changed(self) -> None:
        """ Callback for table selection """
        if self._tables_table.current_selection:
            self.current_table = self.db_handler.data_model.get_table(self._tables_table.current_selection)
        self.current_fields = []
        self._reload_fields_table()
        self.current_record = None
        self._reload_records_table()

    def _on_fields_selection_changed(self) -> None:
        """ Callback for fields selection """
        self.current_fields = self._fields_table.current_selection
        # self._reload_records_table()
    
    def _on_records_selection_changed(self) -> None:
        """ Callback for record selection """
        current_record_id = self._records_table.current_selection
        print("DEBUG 1", current_record_id, self.current_table)
        if current_record_id and self.current_table:
            print("DEBUG 2")
            self.current_record = self.db_handler.get_record(table=self.current_table, display_name=current_record_id)
        else: self.current_record = None
        print("DEBUG 3", self.current_record)
        self._reload_record_form()
        


    def on_button_reload_clicked(self, button:Button) -> None:
        """ """
        self._reload_db()

    def on_button_delete_clicked(self, button:Button) -> None:
        """ """
        # TODO confirmation popup
        pass
