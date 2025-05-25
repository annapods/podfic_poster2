from typing import Any, Optional
from gi.repository.Gtk import Entry, CheckButton, Label, FileChooserButton, \
    SpinButton, Align, Adjustment
from datetime import datetime

from db.objects import Field, TextField, IntField, BoolField, DateField, \
    FilepathField, LengthField
from gui.base_graphics import PlainGrid


class FormField(PlainGrid):
    """ A field in a form, composed mostly of a widget
    Subclasses implement the different data types """
    
    def __init__(self, field:Field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Field information is kept
        self.field = field
        # Any type-specific particularities are handled in the subclasses,
        # including the choice of the widget
        self._init_widget(*args, **kwargs)
        self._format_widget()
        self.attach_next(self._widget, width=1)

    def _format_widget(self) -> None:
        self._widget.set_halign(Align.START)
        # Any setting that can be done at a higher class level: label, editability
        # Mandatory fields are not technically mandatory for sqlite DBHandler,
        # this should be crash tested and handled as an error raised from the DB
        # Editable or not
        self._widget.set_sensitive(self.field.editable)

    def _init_widget(self, *args, **kwargs): raise NotImplementedError
    def set_value(self, value:Any|None): raise NotImplementedError
    def get_value(self) -> Any: raise NotImplementedError
    def set_default(self) -> None:
        if self.field.default_value: self.set_value(self.field.default_value)
        else: self.set_value(None)


class UneditableFormField(FormField):
    """ A form field that isn't editable and just displays a value
    This value can be of any type that implements __str__
    get_value will return the original value in its original type """
    
    def _init_widget(self):
        self._widget = Label()
    
    def set_value(self, value:Optional[Any]=None, text_if_none:Optional[str]=None):
        self.value = value
        if self.value: self._widget.set_label(str(self.value))
        else: self._widget.set_label(text_if_none)
    
    def get_value(self) -> str:
        return self.value


class TextFormField(FormField):
    """ TEXT form field """
    
    def _init_widget(self):
        self._widget = Entry()
        if self.field.default_value:
            self.set_value(self.field.default_value)
        # widget.set_visibility = True  # for passwords and such
        self._widget.set_width_chars(50)  # DEBUG size is that enough?
    
    def set_value(self, value:str|None):
        if value is None: value = ""
        self._widget.set_text(str(value))
    
    def get_value(self) -> str:
        return self._widget.get_text()


class BoolFormField(FormField):
    """ BOOLEAN form field """
    
    def _init_widget(self):
        self._widget = CheckButton()
        self._widget.set_active(self.field.default_value)
    
    def set_value(self, value:bool|None):
        if value is None: value = False
        self._widget.set_active(value)
    
    def get_value(self) -> bool:
        return self._widget.get_active()

   
class DateFormField(TextFormField):
    """ DATE form field """
    
    def _init_widget(self, *args, **kwargs):
        TextFormField._init_widget(self, *args, **kwargs)
    
    def set_value(self, value:str|None):
        if value is None: value = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        self._widget.set_text(value)


class LengthFormField(TextFormField):
    """ LENGTH form field """
    
    def _init_widget(self, *args, **kwargs):
        TextFormField._init_widget(self, *args, **kwargs)
    
    def set_value(self, value:str|None):
        if value is None: value = "00:00:00"
        self._widget.set_text(value)


class IntFormField(FormField):
    """ INTEGER form field """
    # Max number of rows in an sqlite table, probably overkill
    max_int = 9223372036854775807
    
    def _init_widget(self):
        self._widget = SpinButton(adjustment=Adjustment(
            value=0, lower=0, upper=IntFormField.max_int, step_increment=1))
    
    def set_value(self, value:int|None):
        if value == None: value = 0
        self._widget.set_value(value)

    def get_value(self) -> int|None:
        return self._widget.get_value_as_int()


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

    def set_value(self, value:str|None):
        if value == None: value = "."
        self._widget.set_filename(value)
    
    def get_value(self) -> str:
        return self._widget.get_filename()


py_type_to_form_mapping = {
    TextField: TextFormField,
    BoolField: BoolFormField,
    IntField: IntFormField,
    DateField: DateFormField,
    FilepathField: FilepathFormField,
    LengthField: LengthFormField
}

def get_form_field(field:Field) -> FormField:
    return py_type_to_form_mapping[type(field)](field)


