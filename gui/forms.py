from typing import Any, Callable, Dict, List, Optional, Tuple
from gi.repository.Gtk import Entry, CheckButton, Label, FileChooserButton, ComboBoxText, \
    SpinButton, Button, PositionType, ComboBox, RadioButton, Align, Adjustment, \
    STOCK_CANCEL, STOCK_OK
from datetime import datetime


from db.handler import DataHandler, SQLiteHandler
from db.objects import Field, Record, Table, TextField, IntField, BoolField, DateField, FilepathField, LengthField, parse_datetime_format, parse_timedelta_format
from gui.base_graphics import PaddedGrid, PlainGrid
from gui.confirm_dialog import ConfirmDialog, Dialog, InfoDialog
from gui.tables import SingleSelectTable


def find_row_of_record(to_find:Record, options:List[Record]) -> int|None:
    row = None
    for i, option in enumerate(options):
        if option == to_find:
            row = i
    if row is None: print("DEBUG", f"couldn't find {to_find}. Options are: {options}")
    return row

def find_row_of_text(to_find:str, options:List[Record]) -> int|None:
    row = None
    for i, option in enumerate(options):
        if option and option.display_name == to_find:
            row = i
    if row is None: print("DEBUG", f"couldn't find {to_find}. Options are: {options}")
    return row



class FormField(PlainGrid):
    """ A field in a form: label and widget
    Subclasses implement the different data types """
    def __init__(self, field:Field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Field information is kept
        self.field = field
        # Any type-specific particularities are handled in the subclasses,
        # including the choice of the widget
        self._init_widget(*args, **kwargs)
        self._widget.set_halign(Align.START)
        # Any setting that can be done at a higher class level: label, editability
        # Mandatory fields are not technically mandatory for sqlite DBHandler,
        # this should be crash tested and handled as an error raised from the DB
        # Editable or not
        self._widget.set_sensitive(field.editable)
        # Label to the left of the widget
        self.attach_next(self._widget, width=1)
        # DEBUG size
        # using width=N only work if set_column_homogeneous(True) on the grid
        # self._label.set_line_wrap(True)
        # self._label.set_size_request(150,-1)
        # self._widget.set_hexpand(True)
        # self._label.set_size_request(20,20)

    def _init_widget(self, *args, **kwargs): raise NotImplementedError
    def set_value(self, value:Any): raise NotImplementedError
    def get_value(self) -> Any: raise NotImplementedError
    def clear_value(self) -> None: raise NotImplementedError
    def set_default(self) -> None:
        if self.field.default_value: self.set_value(self.field.default_value)
        else: self.clear_value()


class UneditableFormField(FormField):
    """ A form field that isn't editable and just displays a value
    This value can be of any type that implements __str__
    get_value will return the original value in its original type """
    def _init_widget(self):
        self._widget = Label()
    def set_value(self, value:Optional[Any]=None, text_if_none:Optional[str]=None):
        self.value = value
        if self.value:
            self._widget.set_label(str(self.value))
        else:
            self._widget.set_label(text_if_none)
    def get_value(self) -> str:
        return self.value
    def clear_value(self) -> None:
        pass

   
class ExtFormField(FormField):
    """ Any form field that is a reference to another table 
    Several implementations in subclasses """

    def __init__(self, field:Field, table:Table, *args, **kwargs):
        self._db_handler = SQLiteHandler()
        self.current_table = table
        self.current_record = None
        super().__init__(field, *args, **kwargs)

        # Action buttons
        modify_button = Button(label="+")
        modify_button.connect("clicked", self._on_button_modify_clicked)
        self.attach_next(modify_button, PositionType.RIGHT)

    def _init_widget(self) -> None:
        self._options = self._db_handler.get_records(table=self.field.foreign_key_table)
        sort_by_field = self.field.foreign_key_table.sort_rows_by
        self._options.sort(key=lambda record: record.values[sort_by_field], reverse=False)
        if not self.field.mandatory:
            self._options = [None]+self._options

        if not self._options: self._widget = NAExtWidget()
        elif len(self._options) < 5: self._widget = RadioExtWidget(self._options)
        elif len(self._options) < 10: self._widget = DropdownExtWidget(self._options)
        else: self._widget = TableExtWidget(self._options)

        if self.current_record: self._widget.set_value(self.current_record)

    def _on_button_modify_clicked(self, button:Button) -> None:
        """ Callback for record edit button"""
        popup = RecordManagerDialog(
            self._on_record_modified,
            self.current_table, self.current_record)

    def _on_record_modified(self, table:Table, record:Record) -> None:
        """ Callback for the record manager popups that can edit, create and delete records """
        self._init_widget()
        if record:
            self.set_value(record)

    def clear_value(self) -> None:
        self._widget.clear_value()


class NAExtWidget(Label):
    """ An external form field widget with no options available """
    def __init__(self):
        super().__init__()
        self.set_label("No options available")
    def set_value(self) -> None: pass
    def get_value(self) -> Record|None: return None
    def clear_value(self) -> None: pass

class RadioExtWidget(PlainGrid):
    """ An external form field widget with radio button options
    https://stackoverflow.com/questions/391237/pygtk-radio-button """
    def __init__(self, options:List[Record]):
        super().__init__()
        self._options = options
        if len(self._options) == 0: return
        # If the field is not mandatory, none should be an option
        # If there is no default option, it will be the default
        # If there is no default option, no specific button should be selected
        # However, it's not possible to uncheck all radio buttons
        # Workaround: a hidden (or not) empty button for None
        # Source: https://stackoverflow.com/questions/1774161/is-there-a-way-to-uncheck-all-radio-buttons-in-a-group-pygtk
        # Combined with force-hiding it to avoid the refresh of the form by show_all
        # Source: https://github.com/JuliaGraphics/Gtk.jl/issues/609#issuecomment-1013753722
        none_button = RadioButton.new_with_label(None, "")
        if self._options[0] != None:
            none_button.hide()
            none_button.set_no_show_all(True)
            self._options = [None]+self._options
        self.attach_next(none_button)

        for option in self._options[1:]:
            _ = RadioButton.new_with_label_from_widget(none_button, option.display_name)
            self.attach_next(_)
        self._buttons = list(reversed(none_button.get_group()))

    def set_value(self, value:Record):
        row = find_row_of_record(value, self._options)
        if row: self._buttons[row].set_active(True)

    def get_value(self) -> Record|None:
        active_radios = [i for i, radio in enumerate(self._buttons) if radio.get_active()]
        # if not active_radios: return None
        return self._options[active_radios[0]]
    
    def clear_value(self) -> None:
        self._buttons[0].set_active(True)

class DropdownExtWidget(ComboBoxText):
    """ An external form field widget with a dropdown menu """
    def __init__(self, options:List[Record]):
        super().__init__()
        self._options = options
        for i, option in enumerate(self._options):
            self.insert(i, str(i),
                option.display_name if type(option) is Record else "")
        # DEBUG size this one is variable and changes the size of the scrollwindows
    def set_value(self, value:Record):
        row = find_row_of_record(value, self._options)
        self.set_active(row)
    def get_value(self) -> Record|None:
        text = self.get_active_text()
        row = find_row_of_text(text, self._options)
        if row: return self._options[row]
    def clear_value(self) -> None:
        self.set_active(0)

class TableExtWidget(SingleSelectTable):
    """ A table form field widget with single selection and a button to edit records """
    def __init__(self, options:List[Record]):
        def _on_records_selection_changed() -> None:
            """ Callback for record selection """
            self.current_record = self._records_table.current_selection
        super().__init__(_on_records_selection_changed)
        self.reload_table(options)
    def set_value(self, value:Record) -> None:
        self.set_selected(value)
    def get_value(self) -> Record:
        return self.current_selection
    def clear_value(self) -> None:
        self.set_selected(None)


class TextFormField(FormField):
    """ TEXT form field """
    def _init_widget(self):
        self._widget = Entry()
        if self.field.default_value:
            self.set_value(self.field.default_value)
        # widget.set_visibility = True  # for passwords and such
        self._widget.set_width_chars(50)  # DEBUG size is that enough?
    def set_value(self, value:str):
        self._widget.set_text(str(value))
    def get_value(self) -> str:
        return self._widget.get_text()
    def clear_value(self) -> None:
        self.set_value("")

class BoolFormField(FormField):
    """ BOOLEAN form field """
    def _init_widget(self):
        self._widget = CheckButton()
        self._widget.set_active(self.field.default_value)
    def set_value(self, value:bool):
        self._widget.set_active(value)
    def get_value(self) -> bool:
        return self._widget.get_active()
    def clear_value(self):
        self.set_value(False)
    
class DateFormField(TextFormField):
    """ DATE form field """
    def _init_widget(self, *args, **kwargs):
        TextFormField._init_widget(self, *args, **kwargs)
    def clear_value(self):
        self.set_value(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))

class LengthFormField(TextFormField):
    """ LENGTH form field """
    def _init_widget(self, *args, **kwargs):
        TextFormField._init_widget(self, *args, **kwargs)
    def clear_value(self):
        self.set_value("00:00:00")

class IntFormField(FormField):
    """ INTEGER form field """
    # Max number of rows in an sqlite table, probably overkill
    max_int = 9223372036854775807
    def _init_widget(self):
        self._widget = SpinButton(adjustment=Adjustment(
            value=0, lower=0, upper=IntFormField.max_int, step_increment=1))
    def set_value(self, value:int):
        self._widget.set_value(value)
    def get_value(self) -> int|None:
        return self._widget.get_value_as_int()
    def set_default(self) -> None:
        self.set_value(0)

class FilepathFormField(FormField):
    """ FILEPATH form field """
    def _init_widget(self):
        self._widget = FileChooserButton()
        self._widget.set_width_chars(50)  #DEBUG size
        # self._widget.set_current_folder('./db')
        def on_file_picked(file_chooser_button):
              pass  # self.value = file_chooser_button.get_filename()
        self._widget.connect("file-set", on_file_picked)

        if self.field.default_value: self._widget.set_value(self.field.default_value)

    def set_value(self, value:str):
        self._widget.set_filename(value)
    def get_value(self) -> str:
        return self._widget.get_filename()
    def set_default(self) -> None:
        self.set_value(".")


py_type_to_form_mapping = {
    TextField: TextFormField,
    BoolField: BoolFormField,
    IntField: IntFormField,
    DateField: DateFormField,
    FilepathField: FilepathFormField,
    LengthField: LengthFormField
}


class RecordFormGrid(PaddedGrid):
    """ All fields of a record, existing or to-be
    Code interface:
    - last_table
    - last_record
    - get_current_values
    - reset_form_from_record
    - reset_form_from_table
    - reset_form_from_nothing """

    def __init__(self, init_table:Table=None, init_record:Record=None,):
        super().__init__()
        self.set_vexpand(False)

        # Current info and helpers
        self.last_record = init_record
        self.last_table = init_table
        self._form_fields = []
        self._db_handler = SQLiteHandler()

        # Init if possible
        if init_record: self.reset_form_from_record(init_record)
        else: self.reset_form_from_table(init_table)
    
    def _get_form_field_and_label(self, field:Field) -> Tuple[Label,FormField]:
        """ Return an empty form_field from the right type and its label """
        label = Label("*"+field.field_name) if field.mandatory else \
            Label(field.field_name)
        label.set_halign(Align.END)
        if field.foreign_key_table:
            return label, ExtFormField(field, table=field.foreign_key_table)
        return label, py_type_to_form_mapping[type(field)](field)

    def reset_form_from_record(self, record:Record):
        """ Recreate all form fields and fill them with record values """
        self.reset_form_from_nothing()
        self.last_record = record
        self.last_table = record.parent_table

        for field in record.parent_table.fields:
            label, form_field = self._get_form_field_and_label(field)
            self.attach_next(label)
            self.attach_next(form_field, position=PositionType.RIGHT)
            self._form_fields.append(form_field)

        for form_field in self._form_fields:
            if form_field.field.field_name == "ID":
                form_field.set_value(self.last_record.ID)
            elif form_field.field.field_name == "display_name":
                form_field.set_value(self.last_record.display_name)
            elif form_field.field.field_name == "creation_date":
                form_field.set_value(self.last_record.creation_date)
            else:
                value = self.last_record.values[form_field.field]
                form_field.set_value(value)
        self.show_all()

    def reset_form_from_table(self, table:Table):
        """ Recreate all form fields and fill them with default values"""
        self.reset_form_from_nothing()
        self.last_table = table

        for field in table.fields:
            label, form_field = self._get_form_field_and_label(field)
            self.attach_next(label)
            self.attach_next(form_field, position=PositionType.RIGHT)
            self.last_added = label
            self._form_fields.append(form_field)

        for form_field in self._form_fields:
            form_field.set_default()
            
        self.show_all()
    
    def reset_form_from_nothing(self):
        """ Remove form """
        for form_field in self._form_fields:
            self.remove(form_field)
        self._form_fields = []
        self.last_added = None
        self.last_record = None
        self.last_table = None
        self.show_all()

    def get_current_values(self) -> Dict[Field, Any]:
        return {form_field.field:form_field.get_value() for form_field in self._form_fields}


class RecordManagerGrid(RecordFormGrid):
    """ Form + actions on form, in a grid
    If there is a current record:
    - Save button saves modifications to current record
    - Cancel button removes modifications to current record 
    - Delete button deletes the record after confirmation via popup
    If there is not:
    - Save button creates a new record
    - Cancel button resets fields to default values/empty
    - Delete button does nothing after info popup
    #TODO to test """
    def __init__(self, 
            on_change_notify:Callable,
            init_table:Table=None, init_record:Record=None,
            delete_button:bool=True,
        ):
        super().__init__(init_table, init_record)

        def _on_change_notify() -> Tuple[Table, Record]:
            """ Wrapper to add table and record to callable"""
            on_change_notify(self.last_table, self.last_record)
        self._on_change_notify = _on_change_notify

        # Action buttons
        save_button = Button(label="Save")
        save_button.connect("clicked", self._on_button_save_clicked)
        cancel_button = Button(label="Cancel")
        cancel_button.connect("clicked", self._on_button_cancel_clicked)
        if delete_button:
            delete_button = Button(label="Delete")
            delete_button.connect("clicked", self._on_button_delete_clicked)

        button_grid = PaddedGrid()
        button_grid.attach_next(save_button)
        button_grid.attach_next(cancel_button, PositionType.RIGHT)
        if delete_button: button_grid.attach_next(delete_button, PositionType.RIGHT)
        self.attach_next(button_grid)

    def _on_button_save_clicked(self, button:Button):
        # Fetch and validate values
        values = self.get_current_values()
        if not self.last_record:
            self.last_record = Record(self.last_table, values)
            self.last_record.save_to_db(new=True)
            self.last_record = self._db_handler.get_record(
                self.last_record.parent_table, self.last_record.display_name)
            self.reset_form_from_record(self.last_record)
        else:
            for field in values:
                self.last_record.values[field] = values[field]
            self.last_record.save_to_db(new=False)
            self.last_record.recalculate_display_name()
            self.reset_form_from_record(self.last_record)
        self._on_change_notify()

    def _on_button_cancel_clicked(self, button:Button):
        if self.last_record: self.reset_form_from_record(self.last_record)
        elif self.last_table: self.reset_form_from_table(self.last_table)
        else: self.reset_form_from_nothing()

    def _on_button_delete_clicked(self, button:Button):
        if self.last_record:
            popup = ConfirmDialog(self, freeze_app=True)
            response = popup.run()
            if response == Dialog.OK:
                self._db_handler.delete_record_or_fail(self.last_record)
                self.last_record = None
                self.reset_form_from_table(self.last_table)
                self._on_change_notify()
            elif response == Dialog.CANCEL:
                pass
            popup.destroy()
        else:
            popup = InfoDialog("???", "No record to delete", freeze_app=False)
            # response = popup.run()
            # popup.destroy()
            

class RecordManagerDialog(Dialog):
    """ The RecordManagerGrid but in a popup """
    def __init__(self,
            on_change_notify:Callable,
            table:Table, record:Record=None,
            delete_button:bool=True,
            self_destruct_after_call:bool=True):
        super().__init__(title=f"Edit {table.table_name} record", freeze_app=False)

        def _on_change_notify():
            if self_destruct_after_call:
                self.destroy()
            on_change_notify()

        record_manager = RecordManagerGrid(_on_change_notify, table, record, delete_button)

        self._box.add(record_manager)
        self.set_size_request(600,500)  #DEBUG size this one works but at what cost
        self.show_all()
