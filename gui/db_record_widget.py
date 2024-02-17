from typing import Any, Optional
from gui.base_graphics import gi, PaddedGrid
from gi.overrides.Gtk import Entry


def get_field_widget(type:type, default_value:Optional[Any]) -> Any:
    """ Creates a widget from the given type with the given information"""
    if type == str:
        widget = Entry()
        widget.set_text(default_value)
        # widget.set_editable = True
        # widget.set_visibility = True
        return widget
    elif type == int:
        pass
    pass

def get_ext_field_widget(default_value:Optional[Any], table:str) -> Any:
    ext_options = []
    pass

def get_date_field_widget(default_value:Optional[Any]) -> Any:
    # TODO date type??
    pass

def get_time_field_widget(default_value:Optional[Any]) -> Any:
    # TODO time type??
    pass

def get_float_field_widget(default_value:Optional[Any]) -> Any:
    pass

def get_bool_field_widget(default_value:Optional[Any]) -> Any:
    pass

def get_file_field_widget(default_value:Optional[Any]) -> Any:
    # TODO file type??
    pass


class RecordManager(PaddedGrid):
    def __init__(self, db_handler):
        super().__init__()
        self.db_handler = db_handler

    def load_existing(self, table, display_name):
        headers, types, content = self.db_handler.get_table_content_for_gtk_table(
            table, include_display_name=True,
            sort_by=self.db_handler.get_table_sort_by(table),
            where_condition=f"""display_name='{display_name}'""")
        print("DEBUG existing record", headers)
        # ['display_name', 'ao3_tag', 'abbreviation']
        # [<class 'str'>, <class 'str'>, <class 'str'>]
        # [('Choose Not To Use Archive Warnings', 'Choose Not To Use Archive Warnings', 'choose not to use')])

    
    def load_new(self, table):
        test = self.db_handler.get_table_content_for_gtk_table(
            table, include_display_name=True,
            sort_by=self.db_handler.get_table_sort_by(table))
        print("DEBUG new", test)

    def load_empty(self):
        print("DEBUG empty")
        pass