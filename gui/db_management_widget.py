from typing import Any, List, Optional
from gi.repository import Gtk
from gi.overrides.Gtk import Button


from db.handler import SQLiteHandler
from db.objects import Record, Table
from gui.forms import RecordManager
from gui.base_graphics import PaddedFrame, PaddedGrid, ScrollWindow
from gui.tables import MultiSelectTable, SingleSelectTable, TableWidget


class DBManager(PaddedGrid):
    """ Database manager widget, contains tables for table and record selection and a form to edit
    or create records
    Code interface:
    - 
    """

    def __init__(self):
        super().__init__()

        # Current selections and helpers
        self.database_path = ""
        self._db_handler = None
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
        reload_button.connect("clicked", self._on_button_reload_clicked)
        reload_button.vexpand = False

        # Database picker and button in a single frame
        database_frame = PaddedFrame(label="Database")
        database_frame.grid.attach_next(db_picker)
        database_frame.grid.attach_next(reload_button, Gtk.PositionType.RIGHT)
        self.attach_next(database_frame)

        # Tables
        def frame_table(table:TableWidget, label:str) -> PaddedFrame:
            # TODO outside of this class?
            frame = PaddedFrame(label=label)
            frame.grid.attach_next(table)
            return frame

        self._tables_table = SingleSelectTable(self._on_table_selection_changed)
        self.attach_next(frame_table(self._tables_table, "Tables"))
        self._fields_table = MultiSelectTable(self._on_fields_selection_changed)
        self.attach_next(frame_table(self._fields_table, "Table fields"))
        self._records_table = SingleSelectTable(self._on_records_selection_changed)
        self.attach_next(frame_table(self._records_table, "Table records"))

        # Record form
        self._record_grid = RecordManager(on_change_notify=self._on_record_modified)
        record_frame = PaddedFrame(label="Record form")
        # swap default grid for RecordManager
        record_frame.remove(record_frame.grid)
        record_frame.grid = self._record_grid
        record_frame.add(record_frame.grid)
        self.attach_next(
            record_frame, Gtk.PositionType.BOTTOM)  #, 10, 3)
    

    def _reload_db(self) -> None:
        """ """
        self._db_handler = SQLiteHandler(self.database_path)
        self._db_handler.change_db(self.database_path)
        self._record_grid.db_handler = self._db_handler
        self._reload_tables_table()        
        # A few data model stuff that doesn't need to be calculated every time
        self._data_table_table = self._db_handler.data_model.get_table("data_table")
        self._table_name_field = self._data_table_table.get_field("table_name")
    
    def _get_table_from_table_record(self, table_record:Record) -> Table:
        table_name = table_record.values[self._table_name_field]
        table = self._db_handler.data_model.get_table(table_name)
        return table

    def _reload_tables_table(self) -> None:
        """ Reload the tables table, reload in cascade the elements that depend on that table
        This table shows the data_table records """
        records = self._db_handler.get_records(table="data_table")
        self._tables_table.reload_table(records)
        self.current_fields = None
        self._reload_fields_table()
        self._reload_records_table()
    
    def _reload_fields_table(self) -> None:
        """ Reload the fields table for the current table selected, if any, reload in cascade the elements that depend on that table (none currently)
        This table shows the data_field records with a filter on the data_table if applicable"""
        records = self._db_handler.get_records(
            table="data_field",
            where_condition=f'''table_name="{self.current_table.table_name}"''' if self.current_table else ""
        )
        self._fields_table.reload_table(records)

    def _reload_records_table(self) -> None:
        """ Reload the records table, reload in cascade the elements that depend on that table
        This table shows the records of the selected table, if any
        If no table has been selected, or if the table is empty, nothing will be shown, not even column headers """
        if self.current_table:
            records = \
                self._db_handler.get_records(
                    table=self.current_table, sort_by=None
            )
        else:
            records = []
        self._records_table.reload_table(records)
        self.current_record = None
        self._reload_record_form()


    def _reload_record_form(self) -> None:
        """ Reload the record form
        If a table and a record are selected, this form shows the fields and values of the record
        If only a table, the fields are empty
        If no table, nothing """
        if self.current_record and self.current_table:
            self._record_grid.reset_form_from_record(self.current_record)
        elif self.current_table:
            self._record_grid.reset_form_from_table(self.current_table)
        else:
            self._record_grid.reset_form_from_nothing()
            

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
            self.current_table = self._get_table_from_table_record(self._tables_table.current_selection)
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
        self.current_record = self._records_table.current_selection
        self._reload_record_form()

    def _on_button_reload_clicked(self, button:Button) -> None:
        """ Callback for database reload button """
        self._reload_db()

    def _on_record_modified(self) -> None:
        """ Callback for the record manager widget that can edit, create and delete records """
        # The assumption is that the user won't edit the data_table and data_field db tables
        # There is no safegard/failsafe, but come one
        old_record = self.current_record
        self._reload_records_table()
        if old_record:
            self._records_table.set_selected(old_record)


