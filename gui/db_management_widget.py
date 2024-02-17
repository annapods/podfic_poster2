from typing import Any, List, Optional
from gui.base_graphics import PaddedFrame, PaddedGrid, generate_table, init_datastore
from gi.repository import Gtk
from db.db_handler import SQLiteHandler
from gi.overrides.Gtk import TreeSelection, Button

from gui.db_record_widget import RecordManager



class DBManager(PaddedGrid):

    def __init__(self):
        super().__init__()
        self.db_path = None
        self.db_handler = None
        self.current_table = None
        self.current_fields = []
        self.current_record_display_name = ""
        
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
        self._treeviews = {}
        self._datastores = {}
        self._scrollwidgets = {}
        self._frames = {}

        for key, label, selection_mode, on_selection_changed in [
            ["tables", "Tables", "single", self._on_table_selection_changed],
            ["fields", "Table fields", "multiple", self._on_fields_selection_changed],
            ["records", "Table records", "single", self._on_records_selection_changed]
        ]:
            self._scrollwidgets[key], self._treeviews[key], self._datastores[key] = \
                generate_table([], [], [], selection_mode, on_selection_changed)
            self._frames[key] = PaddedFrame(label=label)
            self._frames[key].grid.attach_next(
                self._scrollwidgets[key], width=10, height=3)
            self.attach_next(
                self._frames[key], Gtk.PositionType.BOTTOM, 10, 3)

        # TODO error handling (application level?)

        # Record buttons
        self._record_buttons = {}
        record_buttons_grid = PaddedGrid()
        for i, (key, label, on_button_clicked) in enumerate([
                ("create", "Create", self.on_button_create_clicked),
                ("edit", "Edit", self.on_button_edit_clicked),
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
        self._frames["records"].grid.attach_next(
            record_buttons_grid, Gtk.PositionType.BOTTOM, 3, 1)

        # Record form
        self._reload_db()
        self._record_grid = RecordManager(self.db_handler)
        record_frame = PaddedFrame(label="Record form")
        # swap default grid for RecordManager
        record_frame.remove(record_frame.grid)
        record_frame.grid = self._record_grid
        record_frame.add(record_frame.grid)
        self.attach_next(
            record_frame, Gtk.PositionType.BOTTOM, 10, 3)
        
        # # DEBUG
        # self.db_path = "db/podfics.db"
        # self._reload_db()
        # self.load_values("archive_warning", "Choose Not To Use Archive Warnings")
        
    def load_values(
            self, current_table:Optional[str]=None,
            current_record_display_name:Optional[str]=None
        ) -> None:
        """ """
        self.current_table = current_table
        self._reload_tables_table()
        self._reload_fields_table()
        self._reload_records_table()
        self.current_record_display_name = current_record_display_name
        self._reload_record_form()
    

    def _reload_tables_table(self) -> None:
        """ Reload the tables table """
        column_names, column_types, data = \
            self.db_handler.get_table_content_for_gtk_table(
                table_name="data_table", field_names=[], sort_by=None,
                where_condition=None)
        self._reload_table("tables", column_names, column_types, data)
        self.current_fields = []
    
    def _reload_fields_table(self) -> None:
        """ Reload the fields table """
        column_names, column_types, data = \
            self.db_handler.get_table_content_for_gtk_table(
                table_name="data_field", field_names=[],
                sort_by="COALESCE(table_name, display_order)",
                where_condition=f'''table_name="{self.current_table}"''' \
                    if self.current_table else ""
        )
        self._reload_table("fields", column_names, column_types, data)

    def _reload_records_table(self) -> None:
        """ Reload the records table """
        if self.current_table:
            column_names, column_types, data = \
                self.db_handler.get_table_content_for_gtk_table(
                    table_name=self.current_table, field_names=self.current_fields,
                    include_display_name=True, sort_by=None
            )
        else:
            column_names, column_types, data = [], [], []
        self._reload_table("records", column_names, column_types, data)

    def _reload_table(
            self, table_key:str, column_names:List[str], column_types:List[type], data:List[List[Any]]
            ) -> None:
        """ Reload the table with the given information
        Update rows by reinitializing the datastore
        Update columns by updating the existing treeview"""
        
        self._datastores[table_key] = Gtk.ListStore(*column_types)
        self._datastores[table_key] = init_datastore(self._datastores[table_key], data)

        self._treeviews[table_key].set_model(self._datastores[table_key])
        for column_name in self._treeviews[table_key].get_columns():
            self._treeviews[table_key].remove_column(column_name)
        for i, column_name in enumerate(column_names):
            # Display name can be necessary in the datastore to select a record
            # but it is not shown in the GUI
            if column_name == "display_name": continue
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_name, renderer, text=i)
            column.set_expand(True)
            column.set_resizable(True)
            self._treeviews[table_key].append_column(column)
       
    def _reload_db(self) -> None:
        """ """
        self.db_handler = SQLiteHandler(self.db_path)
        self._record_grid.db_handler = self.db_handler
        self.load_values(None, None)
    
    def _reload_record_form(self) -> None:
        """ """
        if self.current_record_display_name and self.current_table:
            self._record_grid.load_existing(self.current_table, self.current_record_display_name)
        elif self.current_table:
            self._record_grid.load_new(self.current_table)
        else:
            self._record_grid.load_empty()
            

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
            self.current_table = current_id
        self.current_fields = []
        self._reload_fields_table()

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
            print("DEBUG", current_id)  # DEBUG
            self.current_record_display_name = current_id
        


    def on_button_reload_clicked(self, button:Button) -> None:
        """ """
        self._reload_db()

    def on_button_create_clicked(self, button:Button) -> None:
        """ """
        self._record_grid.load_new(
            table=self.current_table)
        pass


    def on_button_edit_clicked(self, button:Button) -> None:
        """ """
        self._record_grid.load_existing(
            table=self.current_table, display_name=self.current_record_display_name)
        pass


    def on_button_delete_clicked(self, button:Button) -> None:
        """ """
        # TODO confirmation popup
        pass
