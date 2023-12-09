from typing import Any, List
from gui.base_graphics import BaseWindow, generate_table, init_treeview, init_datastore, init_scrolled_table
from gi.repository import Gtk
from db.db_handler import SQLiteHandler
from gi.overrides.Gtk import TreeSelection



class DBManagerWindow(BaseWindow):

    def __init__(self):
        super().__init__(title="Database Manager")
        self._current_table = None
        self._db_handler = None
        self._db_path = None
        self._current_fields = []
        self._current_record = ""
        
        # Database picker
        self.pick_db = Gtk.FileChooserButton(
            title="Select the database", action=Gtk.FileChooserAction.OPEN)
        self.pick_db.set_current_folder('./db')
        self.pick_db.connect("file-set", self._on_file_picked)
        frame = Gtk.Frame(label="Database")
        frame.add(self.pick_db)
        self.grid.attach(frame, 0, 0, 100, 1)
        before = frame

        # Tables
        self.frames = {}
        self.treeviews = {}
        self.datastores = {}
        self.scrollwidgets = {}

        for key, label, selection_mode, on_selection_changed in [
            ["tables", "Tables", "single", self._on_table_selection_changed],
            ["fields", "Table fields", "multiple", self._on_fields_selection_changed],
            ["records", "Table records", "single", self._on_records_selection_changed]
        ]:
            self.scrollwidgets[key], self.treeviews[key], self.datastores[key] = \
                generate_table([], [], [], selection_mode, on_selection_changed)
            frame = Gtk.Frame(label=label)
            frame.add(self.scrollwidgets[key])
            self.grid.attach_next_to(
                frame, before, Gtk.PositionType.BOTTOM, 100, 2)
            before = frame

        # TODO reload button
        # TODO run command field + button

        
        # # creating buttons and setting up their events
        # self.buttons = list()
        # button_edit = Gtk.Button(label="Edit")
        # self.buttons.append(button_edit)
        # button_edit.connect("clicked", self.on_button_edit_clicked)
        # # setting up the layout, putting the treeview in a scrollwindow, and the buttons in a row
        # self.grid.attach_next_to(
        #     self.buttons[0], self.scrollable_treelist, Gtk.PositionType.BOTTOM, 1, 1
        # )
        # for i, button in enumerate(self.buttons[1:]):
        #     self.grid.attach_next_to(
        #         button, self.buttons[i], Gtk.PositionType.RIGHT, 1, 1
        #     )

        self.show_all()
        

    def _reload_tables_table(self) -> None:
        """ Reload the tables table """
        column_names, column_types, data = self._db_handler.get_table_contents_for_gui(
            table_name="data_table", field_names=[], sort_by=None, where_condition=None)
        self._reload_table("tables", column_names, column_types, data)
    
    def _reload_fields_table(self) -> None:
        """ Reload the fields table """
        column_names, column_types, data = self._db_handler.get_table_contents_for_gui(
            table_name="data_field", field_names=[], sort_by=None,
            where_condition=f'''table_name="{self._current_table}"''' if self._current_table else ""
        )
        self._reload_table("fields", column_names, column_types, data)

    def _reload_records_table(self) -> None:
        """ Reload the records table """
        if self._current_table:
            column_names, column_types, data = self._db_handler.get_table_contents_for_gui(
                table_name=self._current_table, field_names=self._current_fields, sort_by=None
            )
        else:
            column_names, column_types, data = [], [], []
        self._reload_table("records", column_names, column_types, data)

    def _reload_table(
            self, table_key:str, column_names:List[str], column_types:List[type], data:List[List[Any]]
            ) -> None:
        """ Reload the table with the given information
        Update rows by reinitializing the datastore
        Updatecolumns by updating the existing treeview"""
        
        self.datastores[table_key] = Gtk.ListStore(*column_types)
        self.datastores[table_key] = init_datastore(self.datastores[table_key], data)

        self.treeviews[table_key].set_model(self.datastores[table_key])
        for column_name in self.treeviews[table_key].get_columns():
            self.treeviews[table_key].remove_column(column_name)
        for i, column_name in enumerate(column_names):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_name, renderer, text=i)
            column.set_expand(True)
            column.set_resizable(True)
            self.treeviews[table_key].append_column(column)
       
    
    def _on_file_picked(self, file_chooser_button):
        """ Callback for database file selection """
        self._db_path = file_chooser_button.get_filename()
        self._db_handler = SQLiteHandler(self._db_path)
        self._reload_tables_table()
        self._reload_fields_table()
        self._reload_records_table()

    def _on_table_selection_changed(self, selection:TreeSelection) -> None:
        """ Callback for table selection """
        (model, pathlist) = selection.get_selected_rows()
        for path in pathlist :
            tree_iter = model.get_iter(path)
            current_id = model.get_value(tree_iter, 0)
            self._current_table = current_id
        self._current_fields = []
        self._reload_fields_table()
        self._reload_records_table()

    def _on_fields_selection_changed(self, selection:TreeSelection) -> None:
        """ Callback for fields selection """
        (model, pathlist) = selection.get_selected_rows()
        self._current_fields = []
        for path in pathlist :
            tree_iter = model.get_iter(path)
            current_id = model.get_value(tree_iter, 1)
            self._current_fields.append(current_id)
        self._reload_records_table()
    
    def _on_records_selection_changed(self, selection:TreeSelection) -> None:
        """ Callback for record selection """
        self._current_record = ""
        # TODO


    def on_button_edit_clicked(self, widget):
        """ """
        pass





win = DBManagerWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()