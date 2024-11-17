from typing import Any, List, Optional
from gi.repository.Gtk import Entry, CheckButton, Label, ComboBoxText, SpinButton, Button, PositionType, ComboBox, RadioButton


from db.handler import DataHandler
from db.objects import Field, Record, Table, TextField, IntField, BoolField, DateField, FilepathField, LengthField
from gui.base_graphics import PaddedGrid
from gui.tables import TableGrid


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
        self.set_editable = field.editable
        # Any type-specific particularities are handled in the subclasses, including the choice of the widget
        self._init_widget(*args, **kwargs)
        # Label to the left of the widget
        self.attach_next(self._label)
        self.attach_next(self._widget, position=PositionType.RIGHT)

    def _init_widget(self, *args, **kwargs): raise NotImplementedError
    def set_value(self, value:Any): raise NotImplementedError
    def get_value(self) -> Any: raise NotImplementedError


class UneditableFormField(FormField):
    """ A form field that isn't editable and just displays a text """
    def _init_widget(self, text:str):
        self._widget = Label(text)
    def set_value(self, value:Optional[Record]=None): pass
    def get_value(self) -> None: return None

   
class ExtFormField(FormField):
    """ Any form field that is a reference to another table 
    Several implementations in subclasses """
    def __init__(self, field, options:List[Record], *args, **kwargs):
        if len(options) > 0:
            sort_by_field = options[0].parent_table.sort_rows_by
            options.sort(key=lambda record: record.values[sort_by_field], reverse=False)
        self._options = options
        super().__init__(field, *args, **kwargs)
    def _find_row_of_record(self, to_find:Record) -> int|None:
        row = None
        for i, option in self._options:
            if option == to_find:
                row = i
        if row is None: print("DEBUG", f"{to_find} is not an option for this field. Options are: {self._options}")
        return None
    def _find_row_of_text(self, to_find:str) -> int|None:
        row = None
        for i, option in self._options:
            if option.display_name == to_find:
                row = i
        if row is None: print("DEBUG", f"{to_find} is not an option for this field. Options are: {self._options}")
        return None
    def _init_widget(self): raise NotImplementedError
    def set_value(self, value:Record): raise NotImplementedError
    def get_value(self) -> Record|None: raise NotImplementedError
    

class NAExtFormField(UneditableFormField, ExtFormField):
    """ An external form field with no options available """
    def _init_widget(self):
        super._init_widget(text="No options available")
    def set_value(self, value = None): pass
    def get_value(self) -> None: return None


class RadioExtFormField(ExtFormField):
    """ An external form field with radio button options """
    def _init_widget(self):
        # https://stackoverflow.com/questions/391237/pygtk-radio-button
        if len(self._options) == 0: return
        self._widget = PaddedGrid()
        self._buttons = RadioButton.new_with_label(None, self._options[0].display_name)
        self._widget.attach_next(self._buttons)
        for option in self._options[1:]:
            _ = RadioButton.new_with_label_from_widget(self._buttons, option.display_name)
            self._widget.attach_next(_)
    def set_value(self, value:Record):
        row = self._find_row_of_record(value)
        if row: reversed(self._widget.get_group())[row].set_active(True)
    def get_value(self) -> Record|None:
        active_radios = [i for i, radio in enumerate(reversed(self._buttons.get_group())) if radio.get_active()]
        if not active_radios: return None
        return self._options[active_radios[0]]

class DropdownExtFormField(ExtFormField):
    """ An external form field with a dropdown menu """
    def _init_widget(self):
        self._widget = ComboBoxText()
        for i, option in enumerate(self._options):
            self._widget.insert(i, str(i), option.display_name)
    def set_value(self, value:Record):
        row = self._find_row_of_record(value)
        self._widget.set_active(row)
    def get_value(self) -> Record|None:
        text = self._widget.get_active_text()
        if not text: return None
        row = self._find_row_of_text(text)
        return self._options[row]

class TableExtFormField(ExtFormField):
    """ A table form field with single selection """
    def _init_widget(self, options:List[Record], *args, **kwargs):
        super()._init_widget(options, *args, **kwargs)
        self._widget = TableGrid(label="", selection_mode="single", on_selection_changed=self._on_selection_changed)
        self._current_record = None
        self._widget.reload_table(options)
    def _on_selection_changed(self): pass
    def set_value(self, value:Record): raise NotImplementedError
    def get_value(self) -> Record: raise NotImplementedError


class TextFormField(FormField):
    """ TEXT form field """
    def _init_widget(self):
        self._widget = Entry()
        if self.field.default_value: self._widget.set_text(self.field.default_value)
        # widget.set_visibility = True  # for passwords and such
    def set_value(self, value:str):
        self._widget.set_text(value)
    def get_value(self) -> str:
        return self._widget.get_text()

class BoolFormField(FormField):
    """ BOOLEAN form field """
    def _init_widget(self):
        self._widget = CheckButton()
        self._widget.set_active(self.field.default_value)
    def set_value(self, value:bool):
        self._widget.set_active(value)
    def get_value(self) -> bool:
        return self._widget.get_active()
    
class DateFormField(FormField):
    """ DATE form field """
    def _init_widget(self):
        self._widget = Entry()  # TODO
        if self.field.default_value: self._widget.set_text(self.field.default_value)
    def set_value(self, value:str):
        self._widget.set_text(value)
    def get_value(self) -> str:
        return self._widget.get_text()

class LengthFormField(FormField):
    """ LENGTH form field """
    def _init_widget(self):
        self._widget = Entry()  # TODO
        if self.field.default_value: self._widget.set_text(self.field.default_value)
    def set_value(self, value:str):
        self._widget.set_text(value)
    def get_value(self) -> str:
        return self._widget.get_text()

class IntFormField(FormField):
    """ INTEGER form field """
    def _init_widget(self):
        self._widget = SpinButton()  # climb_rate=0.1, digits = 0)  # DEBUG
    def set_value(self, value:int):
        self._widget.set_value(value)  # DEBUG types...
    def get_value(self) -> int|None:
        return self._widget.get_value_as_int()

class FilepathFormField(FormField):
    """ FILEPATH form field """
    def _init_widget(self):
        self._widget = Entry()  # TODO
        if self.field.default_value: self._widget.set_text(self.field.default_value)
    def set_value(self, value:str):
        self._widget.set_text(value)
    def get_value(self) -> str:
        return self._widget.get_text()


py_type_to_form_mapping = {
    TextField: TextFormField,
    BoolField: BoolFormField,
    IntField: IntFormField,
    DateField: DateFormField,
    FilepathField: FilepathFormField,
    LengthField: LengthFormField
}


class RecordManager(PaddedGrid):
    def __init__(self):  # TODO specify fields? and field order
        super().__init__()

        # Current info and helpers
        self.db_handler = DataHandler()
        self._record = None
        self._table = None
        self._form_fields = []

        # Form fields and the corresponding grid will be filled by init_form_from_record or init_form_from_table
        self._form_fields_grid = PaddedGrid()
        self.attach_next(self._form_fields_grid)

        # Action buttons
        save_button = Button(label="Save")
        save_button.connect("clicked", self._on_button_save_clicked)
        cancel_button = Button(label="Cancel")
        cancel_button.connect("clicked", self._on_button_cancel_clicked)
        delete_button = Button(label="Delete")
        delete_button.connect("clicked", self._on_button_delete_clicked)

        self.attach_next(save_button)
        self.attach_next(cancel_button, PositionType.RIGHT)
        self.attach_next(delete_button, PositionType.RIGHT)
        # Action buttons
        # self.attach_next(
        #     action_buttons_grid, PositionType.BOTTOM, 3, 1)
    
    def _get_form_field(self, field:Field, value:Optional[Any]=None) -> FormField:
        """ Return a form_field from the right type """
        if field.foreign_key_table:
            options = self.db_handler.get_records(table=field.foreign_key_table)
            if len(options) == 0: return NAExtFormField(field, options)
            if len(options) > 5: return RadioExtFormField(field, options)
            if len(options) > 10: return RadioExtFormField(field, options)
            return ExtFormField(field, options)
            # if len(options) > 10: return DropdownExtFormField(field, options)
            # return TableExtFormField(field, options)
        return py_type_to_form_mapping[type(field)](field)

    def _empty_form(self):
        for form_field in self._form_fields:
            self._form_fields_grid.remove(form_field)
        self._form_fields = []
        self._form_fields_grid.last_added = None
    
    def _update_record_from_form(self):
        for form_field in self._form_fields:
            self._record.values[form_field.field] = form_field.get_value()
    
    def _update_form_from_record(self):
        for form_field in self._form_fields:
            if form_field.field.field_name == "ID":
                form_field.set_value(self._record.ID)
            elif form_field.field.field_name == "display_name" or form_field.field.field_name == "creation_date":
                print("DEBUG 3 ???")
            else:
                value = self._record.values[form_field.field]
                form_field.set_value(value)
    
    def _update_form_from_default(self):
        for form_field in self._form_fields:
            if form_field.field.default_value != "" and form_field.field.default_value != None:
                form_field.set_value(form_field.field.default_value)

    def init_form_from_record(self, record:Record):
        """ Recreate all form fields and fill them with record values """
        self._empty_form()
        self._record = record
        self._table = record.parent_table
        for field in record.parent_table.fields:
            form_field = self._get_form_field(field)
            self._form_fields_grid.attach_next(form_field)
            self._form_fields.append(form_field)
        self._update_form_from_record()
        self.show_all()

    def init_form_from_table(self, table:Table):
        """ Recreate all form fields and fill them with default values"""
        self._empty_form()
        self._record = None
        self._table = table
        for field in table.fields:
            form_field = self._get_form_field(field)
            self._form_fields_grid.attach_next(form_field)
            self._form_fields.append(form_field)
            # form_field.show()
            # form_field.show_all()
        self._update_form_from_default()
        self.show_all()
    
    def init_form_from_nothing(self):
        """ Remove form """
        self._empty_form()
        self._record = None
        self._table = None
        self.show_all()

    def _on_button_save_clicked(self, button:Button):
        if not self._record:
            values = {form_field.field: form_field.get_value() for form_field in self._form_fields}
            self._record = Record(self._table, values)
            self._record.save_to_db(new=True)
        else:
            self._update_record_from_form()
            self._record.save_to_db(new=False)
        # DEBUG TODO 1 needs to also update the table with records
        # reproduce: choose a record, edit a field included in the display name
        # then select a second record, then reselect the one you edited
        # the display name for that row isn't in the database anymore

    def _on_button_cancel_clicked(self, button:Button):
        if self._record: self._update_form_from_record()
        elif self._table: self._update_form_from_default()
        else: pass

    def _on_button_delete_clicked(self, button:Button):
        if self._record: self.db_handler.delete_record_or_fail(self._record)
        else: pass
