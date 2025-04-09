from typing import Any, Callable, Dict, List, Optional, Tuple
from gi.repository.Gtk import Entry, CheckButton, Label, FileChooserButton, ComboBoxText, \
    SpinButton, Button, PositionType, ComboBox, RadioButton, Align, Adjustment, \
    STOCK_CANCEL, STOCK_OK
from datetime import datetime


from db.handler import DataHandler, SQLiteHandler
from db.objects import Field, Record, Table, TextField, IntField, BoolField, DateField, FilepathField, LengthField, parse_datetime_format, parse_timedelta_format
from gui.base_graphics import PaddedFrame, PaddedGrid
from gui.confirm_dialog import ConfirmDialog, Dialog
from gui.tables import SingleSelectTable


class FormField(PaddedGrid):
    """ A field in a form: label and widget
    Subclasses implement the different data types """
    def __init__(self, field:Field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Field information is kept
        self.field = field
        # Any setting that can be done at a higher class level: label, editability
        # Mandatory fields are not technically mandatory for sqlite DBHandler, TODO see if we can do something about that
        self._label = Label("*"+field.field_name) if field.mandatory else Label(field.field_name)
        self._label.set_halign(Align.END)
        # Any type-specific particularities are handled in the subclasses, including the choice of the widget
        self._init_widget(*args, **kwargs)
        self._widget.set_halign(Align.START)
        # Editable or not
        self._widget.set_sensitive(field.editable)
        # Label to the left of the widget
        self.attach_next(self._label)
        self.attach_next(self._widget, position=PositionType.RIGHT)

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

    def __init__(self, field:Field, options:List[Record], *args, **kwargs):
        if len(options) > 0:
            sort_by_field = options[0].parent_table.sort_rows_by
            options.sort(key=lambda record: record.values[sort_by_field], reverse=False)
        self._options = options
        if not field.mandatory:
            self._options = [None]+self._options
        super().__init__(field, *args, **kwargs)

    def _find_row_of_record(self, to_find:Record) -> int|None:
        row = None
        for i, option in enumerate(self._options):
            if option == to_find:
                row = i
        if row is None: print("DEBUG", f"{to_find} is not an option for this field. Options are: {self._options}")
        return row
    
    def _find_row_of_text(self, to_find:str) -> int|None:
        row = None
        if to_find == "": return 0
        for i, option in enumerate(self._options):
            if option and option.display_name == to_find:
                row = i
        if row is None: print("DEBUG", f"{to_find} is not an option for this field. Options are: {self._options}")
        return row
    
    def _find_row_of_ID(self, to_find:int) -> Record|None:
        row = None
        for i, option in enumerate(self._options):
            if option.ID == to_find:
                row = i
        if row is None: print("DEBUG", f"{to_find} is not an option for this field. Options are: {self._options}")
        return row
    

class NAExtFormField(UneditableFormField, ExtFormField):
    """ An external form field with no options available """
    def __init__(self, field, options, *args, **kwargs):
        ExtFormField.__init__(self, field, options, *args, **kwargs)
        UneditableFormField.__init__(self, field, *args, **kwargs)
    def _init_widget(self):
        UneditableFormField._init_widget(self)
        UneditableFormField.set_value(self, None, "No options available")
    def set_value(self, value = None): pass
    def get_value(self) -> None: return None
    def clear_value(self) -> None: pass


class RadioExtFormField(ExtFormField):
    """ An external form field with radio button options """
    def _init_widget(self):
        # https://stackoverflow.com/questions/391237/pygtk-radio-button
        if len(self._options) == 0: return
        self._widget = PaddedGrid()

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
        self._widget.attach_next(none_button)

        for option in self._options[1:]:
            _ = RadioButton.new_with_label_from_widget(none_button, option.display_name)
            self._widget.attach_next(_)
        self._buttons = list(reversed(none_button.get_group()))
        self.set_default()

    def set_value(self, value:Record):
        row = self._find_row_of_record(value)
        if row: self._buttons[row].set_active(True)

    def get_value(self) -> Record|None:
        active_radios = [i for i, radio in enumerate(self._buttons) if radio.get_active()]
        # if not active_radios: return None
        return self._options[active_radios[0]]
    
    def clear_value(self) -> None:
        self._buttons[0].set_active(True)

class DropdownExtFormField(ExtFormField):
    """ An external form field with a dropdown menu """
    def _init_widget(self):
        self._widget = ComboBoxText()
        for i, option in enumerate(self._options):
            self._widget.insert(i, str(i),
                option.display_name if type(option) is Record else "")
        self.set_default()
    def set_value(self, value:Record):
        row = self._find_row_of_record(value)
        self._widget.set_active(row)
    def get_value(self) -> Record|None:
        text = self._widget.get_active_text()
        if not text: return None
        row = self._find_row_of_text(text)
        return self._options[row]
    def clear_value(self) -> None:
        self._widget.set_active(0)

class TableExtFormField(ExtFormField):
    """ A table form field with single selection """
    def _init_widget(self, options:List[Record], *args, **kwargs):
        super()._init_widget(options, *args, **kwargs)
        self._widget = None  # SingleSelectTable(label="", selection_mode="single", on_selection_changed=self._on_selection_changed)
        self._current_record = None
        self._widget.reload_table(options)
    def _on_selection_changed(self): pass
    def set_value(self, value:Record): raise NotImplementedError
    def get_value(self) -> Record: raise NotImplementedError
    def clear_value(self) -> None: raise NotImplementedError


class TextFormField(FormField):
    """ TEXT form field """
    def _init_widget(self):
        self._widget = Entry()
        if self.field.default_value:
            self.set_value(self.field.default_value)
        # widget.set_visibility = True  # for passwords and such
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
        self._widget.set_width_chars(50)
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


class RecordForm(PaddedGrid):
    """ All fields of a record, existing or to-be
    Code interface:
    - last_table
    - last_record
    - get_current_values
    - reset_form_from_record
    - reset_form_from_table
    - reset_form_from_nothing """

    def __init__(self, db_handler:SQLiteHandler):  # TODO specify fields? and field order
        super().__init__()

        # Current info and helpers
        self.last_record = None
        self.last_table = None
        self._form_fields = []
        self._db_handler = db_handler

        # Form fields and the corresponding grid will be filled by reset_form_from_record or reset_form_from_table
        self._form_fields_grid = PaddedGrid()
        self.attach_next(self._form_fields_grid)
    
    def _get_form_field(self, field:Field) -> FormField:
        """ Return an empty form_field from the right type """
        if field.foreign_key_table:
            options = self._db_handler.get_records(table=field.foreign_key_table)
            if len(options) == 0: return NAExtFormField(field, options)
            if len(options) < 5: return RadioExtFormField(field, options)
            if len(options) < 10: return DropdownExtFormField(field, options)
            return DropdownExtFormField(field, options)
            # return TableExtFormField(field, options)
        return py_type_to_form_mapping[type(field)](field)

    def reset_form_from_record(self, record:Record):
        """ Recreate all form fields and fill them with record values """
        self.reset_form_from_nothing()
        self.last_record = record
        self.last_table = record.parent_table

        for field in record.parent_table.fields:
            form_field = self._get_form_field(field)
            self._form_fields_grid.attach_next(form_field)
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
            form_field = self._get_form_field(field)
            self._form_fields_grid.attach_next(form_field)
            self._form_fields.append(form_field)

        for form_field in self._form_fields:
            form_field.set_default()
            
        self.show_all()
    
    def reset_form_from_nothing(self):
        """ Remove form """
        for form_field in self._form_fields:
            self._form_fields_grid.remove(form_field)
        self._form_fields = []
        self._form_fields_grid.last_added = None
        self.last_record = None
        self.last_table = None
        self.show_all()

    def get_current_values(self) -> Dict[Field, Any]:
        return {form_field.field:form_field.get_value() for form_field in self._form_fields}


class RecordManagerGrid(PaddedGrid):
    """ Form + save + cancel + delete, in a grid
    For directly in a main window """
    def __init__(self, on_change_notify:Callable):  # TODO specify fields? and field order
        super().__init__()

        # Current info and helpers
        self._db_handler = SQLiteHandler()
        self._on_change_notify = on_change_notify
        self.form = RecordForm(self._db_handler)
        self.attach_next(self.form)

        # Action buttons
        save_button = Button(label="Save")
        save_button.connect("clicked", self._on_button_save_clicked)
        cancel_button = Button(label="Cancel")
        cancel_button.connect("clicked", self._on_button_cancel_clicked)
        delete_button = Button(label="Delete")
        delete_button.connect("clicked", self._on_button_delete_clicked)

        # TODO button grid
        self.form.attach_next(save_button)
        self.form.attach_next(cancel_button, PositionType.RIGHT)
        self.form.attach_next(delete_button, PositionType.RIGHT)
        # Action buttons
        # self.attach_next(
        #     action_buttons_grid, PositionType.BOTTOM, 3, 1)

    def _on_button_save_clicked(self, button:Button):
        # Fetch and validate values
        values = self.form.get_current_values()
        if not self.form.last_record:
            self.form.last_record = Record(self.form.last_table, values)
            self.form.last_record.save_to_db(new=True)
            self.form.reset_form_from_record(self.form.last_record)
        else:
            for field in values:
                self.form.last_record.values[field] = values[field]
            self.form.last_record.save_to_db(new=False)
            self.form.last_record.recalculate_display_name()
            self.form.reset_form_from_record(self.form.last_record)
        self._on_change_notify()

    def _on_button_cancel_clicked(self, button:Button):
        if self.form.last_record: self.form.reset_form_from_record(self.form.last_record)
        elif self.form.last_table: self.form.reset_form_from_table(self.form.last_table)
        else: self.form.reset_form_from_nothing()

    def _on_button_delete_clicked(self, button:Button):
        if self.form.last_record:
            popup = ConfirmDialog(self, freeze_app=True)
            response = popup.run()
            if response == Dialog.OK:
                self._db_handler.delete_record_or_fail(self.form.last_record)
                self.form.last_record = None
                self.form.reset_form_from_table(self.form.last_table)
                self._on_change_notify()
            elif response == Dialog.CANCEL:
                pass
            popup.destroy()
            


class RecordManagerDialog(Dialog):
    """ Form + save + cancel + delete, in a popup
    # TODO define user interface: what popups do we want, with what buttons, when? """
    def __init__(self,
            on_change_notify:Callable,
            db_handler:SQLiteHandler, table:Table, record:Record=None,
            self_destruct_after_call:bool=True,):
        super().__init__(title="Edit record", freeze_app=False)
        # self.set_default_size(150, 100)

        self._db_handler = db_handler

        def _on_change_notify() -> Tuple[Table, Record]:
            """ Wrapper to add table and record to callable"""
            on_change_notify(self.form.last_table, self.form.last_record)
            if self_destruct_after_call:
                self.destroy()
        self._on_change_notify = _on_change_notify
        
        self.form = RecordForm(db_handler)
        self._box.add(self.form)

        if record: self.form.reset_form_from_record(record)
        else: self.form.reset_form_from_table(table)

        # Action buttons
        save_button = Button(label="Save")
        save_button.connect("clicked", self._on_button_save_clicked)
        cancel_button = Button(label="Cancel")
        cancel_button.connect("clicked", self._on_button_cancel_clicked)
        delete_button = Button(label="Delete")
        delete_button.connect("clicked", self._on_button_delete_clicked)

        # TODO button grid
        self.form.attach_next(save_button)
        self.form.attach_next(cancel_button, PositionType.RIGHT)
        self.form.attach_next(delete_button, PositionType.RIGHT)
        # Action buttons
        # self.attach_next(
        #     action_buttons_grid, PositionType.BOTTOM, 3, 1)

        self.show_all()

    def _on_button_save_clicked(self, button:Button):
        # Fetch and validate values
        values = self.form.get_current_values()
        if not self.form.last_record:
            self.form.last_record = Record(self.form.last_table, values)
            self.form.last_record.save_to_db(new=True)
            self.form.reset_form_from_record(self.form.last_record)
        else:
            for field in values:
                self.form.last_record.values[field] = values[field]
            self.form.last_record.save_to_db(new=False)
            self.form.last_record.recalculate_display_name()
            self.form.reset_form_from_record(self.form.last_record)
        self._on_change_notify()

    def _on_button_cancel_clicked(self, button:Button):
        if self.form.last_record: self.form.reset_form_from_record(self.form.last_record)
        elif self.form.last_table: self.form.reset_form_from_table(self.form.last_table)
        else: self.form.reset_form_from_nothing()

    def _on_button_delete_clicked(self, button:Button):
        if self.form.last_record:
            popup = ConfirmDialog(self, freeze_app=True)
            response = popup.run()
            if response == Dialog.OK:
                self._db_handler.delete_record_or_fail(self.form.last_record)
                self.form.last_record = None
                self.form.reset_form_from_table(self.form.last_table)
                self._on_change_notify()
            elif response == Dialog.CANCEL:
                pass
            popup.destroy()
            