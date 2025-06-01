from typing import Callable, List
from gi.repository import Gtk
from gi.overrides.Gtk import Button


from db.handler import SQLiteHandler
from db.objects import Record, Table
from gui.bricks.forms.record_managers import RecordManagerDialog, RecordManagerGrid
from gui.bricks.containers import PaddedFrame, PaddedGrid
from gui.bricks.tables import MultiSelectTable, SingleSelectTable, TableWidget


class DBManager(PaddedGrid):
    """ Database manager widget, contains tables for table and record selection and a form to edit
    or create records
    Code interface, to be used for setting up tests only:
    - self.database_path, str
    - self.current_table, Table
    - self.current_fields, List[Field]
    - self.current_record, Record
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
        self._db_picker = db_picker

        # Reload database button
        reload_button = Gtk.Button(label="Reload")
        reload_button.connect("clicked", self._on_button_reload_clicked)
        reload_button.vexpand = False

        # Database picker and button in a single frame
        database_frame = PaddedFrame(label="Database")
        database_frame.grid.attach_next(self._db_picker)
        database_frame.grid.attach_next(reload_button, Gtk.PositionType.RIGHT)
        self.attach_next(database_frame)

        # Tables
        def frame_grid(table:TableWidget, label:str) -> PaddedFrame:
            # TODO outside of this class?
            frame = PaddedFrame(label=label)
            frame.grid.attach_next(table)
            return frame

        self._tables_table = SingleSelectTable(self._on_table_selection_changed)
        self.attach_next(frame_grid(self._tables_table, "Tables"))
        self._fields_table = MultiSelectTable(self._on_fields_selection_changed)
        self.attach_next(frame_grid(self._fields_table, "Table fields"))
        self._records_table = SingleSelectTable(self._on_records_selection_changed)
        self.attach_next(frame_grid(self._records_table, "Table records"))

        # Record form
        self._record_grid = RecordManagerGrid(on_change_notify=self._on_record_modified)
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
        self._tables_table.load_options(records)
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
        self._fields_table.load_options(records)

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
        self._records_table.load_options(records)
        self.current_record = None
        self._reload_record_form()


    def _reload_record_form(self) -> None:
        """ Reload the record form
        If a table and a record are selected, this form shows the fields and values of the record
        If only a table, the fields are empty
        If no table, nothing """
        if self.current_record and self.current_table:
            self._record_grid.form.reset_form_from_record(self.current_record)
        elif self.current_table:
            self._record_grid.form.reset_form_from_table(self.current_table)
        else:
            self._record_grid.form.reset_form_from_nothing()
            

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

    def set_db(self, db_path:str) -> None:
        """ For test purposes """
        self._db_picker.set_filename(db_path)
        self.database_path = db_path
        self._reload_db()

    def set_table(self, table:Table|str|Record) -> None:
        """ For test purposes """
        if type(table) is str:
            table = self._db_handler.get_record(
                table=self._data_table_table, display_name=table)
        elif type(table) is Table:
            table = self._db_handler.get_record(
                table=self._data_table_table, display_name=table.display_name)
        self._tables_table.set_selected(table)
    
    def set_record(self, record:Record|str) -> None:
        """ For test purposes """
        if type(record) is str:
            record = self._db_handler.get_record(
                table=self.current_table, display_name=record)
        self._records_table.set_selected(record)

    def tests(self):
        self.set_db("/home/anna/Documents/code/podfic_poster2/db/podfics.db")
        self.set_table("contribution")
        # self.set_record("No Archive Warnings Apply")
        # self.info(f"{self.current_record}")



class DBManager2(PaddedGrid):
    """ Database manager widget, contains tables for table and record selection and action buttons
    Code interface, to be used for setting up tests only:
    - self.database_path, str
    - self.current_table, Table
    - self.current_fields, List[Field]
    - 
    """

    def __init__(self):
        super().__init__()

        # Current selections and helpers
        self.database_path = ""
        self._db_handler = None
        self.current_table = None
        
        # Database picker
        db_picker = Gtk.FileChooserButton(
            title="Select the database", action=Gtk.FileChooserAction.OPEN)
        db_picker.set_current_folder('./db')
        db_picker.connect("file-set", self._on_file_picked)
        self._db_picker = db_picker

        # Reload database button
        reload_button = Gtk.Button(label="Reload")
        reload_button.connect("clicked", self._on_button_reload_clicked)
        reload_button.vexpand = False

        # Database picker and button in a single frame
        database_frame = PaddedFrame(label="Database")
        database_frame.grid.attach_next(self._db_picker)
        database_frame.grid.attach_next(reload_button, Gtk.PositionType.RIGHT)
        self.attach_next(database_frame)

        # Tables
        def frame_grid(table:PaddedGrid, label:str) -> PaddedFrame:
            # TODO outside of this class?
            frame = PaddedFrame(label=label)
            frame.grid.attach_next(table)
            table.set_column_homogeneous(True)  #DEBUG size
            return frame

        self._tables_table = SingleSelectTable(self._on_table_selection_changed)
        self.attach_next(frame_grid(self._tables_table, "Tables"))
        self._fields_table = MultiSelectTable(lambda: None)
        self.attach_next(frame_grid(self._fields_table, "Table fields"))
        self._records_table = TableManager(lambda: None)  # TODO
        self.attach_next(frame_grid(self._records_table, "Table records"))
    

    def _reload_db(self) -> None:
        """ """
        self._db_handler = SQLiteHandler(self.database_path)
        self._db_handler.change_db(self.database_path)
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
        self._tables_table.load_options(records)
        self._reload_fields_table()
        self._reload_records_table()
    
    def _reload_fields_table(self) -> None:
        """ Reload the fields table for the current table selected, if any, reload in cascade the elements that depend on that table (none currently)
        This table shows the data_field records with a filter on the data_table if applicable"""
        records = self._db_handler.get_records(
            table="data_field",
            where_condition=f'''table_name="{self.current_table.table_name}"''' if self.current_table else ""
        )
        self._fields_table.load_options(records)

    def _reload_records_table(self) -> None:
        """ Reload the records table
        This table shows the records of the selected table, if any
        If no table has been selected, or if the table is empty, nothing will be shown,
        not even column headers """
        self._records_table.load_options(table=self.current_table)

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
            self.current_table = self._get_table_from_table_record(
                self._tables_table.current_selection)
        self.current_fields = []
        self._reload_fields_table()
        self._reload_records_table()

    def _on_button_reload_clicked(self, button:Button) -> None:
        """ Callback for database reload button """
        self._reload_db()

    def set_db(self, db_path:str) -> None:
        """ For test purposes """
        self._db_picker.set_filename(db_path)
        self.database_path = db_path
        self._reload_db()

    def set_table(self, table:Table|str|Record) -> None:
        """ For test purposes """
        if type(table) is str:
            table = self._db_handler.get_record(
                table=self._data_table_table, display_name=table)
        elif type(table) is Table:
            table = self._db_handler.get_record(
                table=self._data_table_table, display_name=table.display_name)
        self._tables_table.set_selected(table)
        self._on_table_selection_changed()  # TODO DEBUG this should not be necessary
    
    def set_record(self, record:Record|str) -> None:
        """ For test purposes """
        self._records_table.set_selected(record)

    def tests(self):
        self.set_db("/home/anna/Documents/code/podfic_poster2/db/podfics.db")
        self.set_table("contribution")
        # self.set_record("No Archive Warnings Apply")



class TableManager(PaddedGrid):

    def __init__(
            self, on_selection_changed:Callable=lambda: None,
            init_table:Table=None, init_record:Record=None,
            init_options:List[Record]=None):
        super().__init__()

        self._db_handler = SQLiteHandler()
        self.current_table = init_table
        self.current_record = init_record

        def _on_records_selection_changed() -> None:
            """ Callback for record selection """
            self.current_record = self._records_table.current_selection
            on_selection_changed()
        self._on_records_selection_changed = _on_records_selection_changed

        self._records_table = SingleSelectTable(self._on_records_selection_changed)
        self._records_table.set_column_homogeneous(True)
        if init_options: self.load_options(init_options)
        self.attach_next(self._records_table, width=5)

        # Action buttons
        modify_button = Button(label="Modify")
        modify_button.connect("clicked", self._on_button_modify_clicked)
        self.attach_next(modify_button, Gtk.PositionType.RIGHT)

    def load_options(self, records:List[Record]|None=None, table:Table=None) -> None:
        """ Reload the records table """
        # Define current table
        if table: self.current_table = table
        elif records: self.current_table = records[0].parent_table
        # Fetch records if only table is given
        if self.current_table and not records:
            records = self._db_handler.get_records(
                table=self.current_table, sort_by=None)
        # Reset table records
        self._records_table.load_options(records)
        # self._records_table.set_selected(self.current_record)

    def _on_button_modify_clicked(self, button:Button) -> None:
        """ Callback for record edit button"""
        popup = RecordManagerDialog(
            table=self.current_table,
            record=self.current_record,
            on_change_notify=self._on_record_modified)

    def _on_record_modified(self, record:Record) -> None:
        """ Callback for the record manager popups that can edit, create and delete records """
        self.load_options()
        if record and record.parent_table == self.current_table:
            self.set_record(record)

    def set_record(self, record:Record|str) -> None:
        """  """
        if type(record) is str:
            record = self._db_handler.get_record(
                table=self.current_table, display_name=record)
        self._records_table.set_selected(record)
        self._on_records_selection_changed()  # TODO DEBUG this should not be necessary
