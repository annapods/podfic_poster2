from typing import Any, Optional
from db.db_objects import Field, Record, Table
from gui.base_graphics import gi, PaddedGrid
from gi.repository.Gtk import Entry, CheckButton, Label, ComboBoxText, SpinButton, Button, PositionType




class FormField(PaddedGrid):
    def __init__(self, field:Field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field = field
        self._label = Label("*"+field.field_name) if field.mandatory else Label(field.field_name)
        self._init_widget()
        self.attach_next(self._label)
        self.attach_next(self._widget, position=PositionType.RIGHT)

    def _init_widget(self):
        raise NotImplementedError
    
    def set_value(self, value:Any):
        raise NotImplementedError

    def get_value(self) -> Any:
        raise NotImplementedError


class TextFormField(FormField):
    def _init_widget(self):
        self._widget = Entry()
        if self.field.default_value: self._widget.set_text(self.field.default_value)
        # widget.set_mandatory = mandatory  # TODO debug
        # widget.set_editable = True
        # widget.set_visibility = True  # for passwords and such

    def set_value(self, value:str):
        self._widget.set_text(value)
    
    def get_value(self) -> str:
        return self._widget.get_text()

class BoolFormField(FormField):
    def _init_widget(self):
        self._widget = CheckButton()
        self._widget.set_action_name("Test")  # TODO debug
        self._widget.set_active(self.field.default_value)
    
    def set_value(self, value:bool):
        self._widget.set_active(value)

    def get_value(self) -> bool:
        return self._widget.get_active()

class ExtFormField(FormField):
    def _init_widget(self):
        options = []
        # options = field.foreign_key_table
        # how to get to the db handler to get the options?
        self._widget = ComboBoxText()
        # need to be sorted
        for i, option in options:
            self._widget.insert(i, "return value? "+str(i), option)

    def set_value(self, value):
        self._widget.set_value(self.field.default_value)  # ??

    def get_value(self):
        self._widget.get_value()  # ??

class DateFormField(FormField):
    def _init_widget(self):
        pass

    def set_value(self, value):
        pass

    def get_value(self):
        pass

class LengthFormField(FormField):
    def _init_widget(self):
        pass

    def set_value(self, value):
        pass

    def get_value(self):
        pass

class IntFormField(FormField):
    def _init_widget(self):
        self._widget = SpinButton(climb_rate=0.1, digits = 0)

    def set_value(self, value):
        self._widget.set_value(value)  # DEBUG types...

    def get_value(self):
        self._widget.get_value()  # ??

class FilepathFormField(FormField):
    def _init_widget(self):
        pass

    def set_value(self, value):
        pass

    def get_value(self):
        pass

class NotImplementedField(FormField):
    def _init_widget(self):
        self._widget = Label()
    def set_value(self, value):
        self._widget.set_label(value)
    def get_value(self):
        return self._widget.get_label()

def get_form_field(field:Field, value:Optional[Any]=None) -> FormField:
    """ Return a form_field from the right type """
    if field.foreign_key_table: return ExtFormField(field)
    if field.type == "TEXT": return TextFormField(field)
    elif field.type == "BOOLEAN": return BoolFormField(field)
    elif field.type == "INTEGER": return IntFormField(field)
    # elif field.type == "DATE": return DateFormField(field)
    # elif field.type == "FILEPATH": return FilepathFormField(field)
    # elif field.type == "LENGTH": return LengthFormField(field)
    # else: assert False, "Unknown file type "+field.type
    else: return NotImplementedField(field)


class RecordManager(PaddedGrid):
    def __init__(self, db_handler):
        super().__init__()
        self.db_handler = db_handler
        self._record = None
        self._table = None
        self._form_fields = []
        self._form_fields_grid = PaddedGrid()
        # Empty form fields grid will be filled by init_form_from_record or init_form_from_table
        self.attach_next(self._form_fields_grid)
        # Action buttons
        self._action_buttons = {}
        action_buttons_grid = PaddedGrid()
        for i, (key, label, on_button_clicked) in enumerate([
                ("save", "Save", self._on_button_save_clicked),
                ("cancel", "Cancel", self._on_button_cancel_clicked)
            ]):
            self._action_buttons[key] = Button(label=label)
            self._action_buttons[key].connect("clicked", on_button_clicked)
            if i == 0:
                action_buttons_grid.attach(self._action_buttons[key], 0,0,1,1)
            else:
                action_buttons_grid.attach_next(
                    self._action_buttons[key],
                    PositionType.RIGHT, 1, 1)
        self.attach_next(
            action_buttons_grid, PositionType.BOTTOM, 3, 1)
    
    def _empty_form(self):
        for form_field in self._form_fields:
            self._form_fields_grid.remove(form_field)
        self._form_fields = []
        self._form_fields_grid.last_added = None
    
    def _update_record_from_form(self):
        for form_field in self._form_fields:
            self._record[form_field.field] = form_field.get_value()
    
    def _update_form_from_record(self):
        for form_field in self._form_fields:  # DEBUG TODO some fields are not editable -> where/when to handle that?
            # Could be at db model (makes a lot of sense)
            # Or filter out the technical fields
            form_field.set_value(self._record.values[form_field.field])
    
    def _update_form_from_default(self):
        for form_field in self._form_fields:
            if form_field.field.default_value != "" and form_field.field.default_value != None:
                form_field.set_value(form_field.field.default_value)

    def init_form_from_record(self, record:Record):
        """ Recreate all form fields and fill them with record values """
        print("DEBUG", "init from record")
        self._empty_form()
        self._record = record
        self._table = record.parent_table
        for field in record.parent_table.fields:
            form_field = get_form_field(field)
            self._form_fields_grid.attach_next(form_field)
            self._form_fields.append(form_field)
        self._update_form_from_record()
        self.show_all()

    def init_form_from_table(self, table:Table):
        """ Recreate all form fields and fill them with default values"""
        print("DEBUG", "init from table")
        self._empty_form()
        self._record = None
        self._table = table
        for field in table.fields:
            print("DEBUG", field.field_name)
            form_field = get_form_field(field)
            if form_field:  # DEBUG for now, as not every type has been implemented
                self._form_fields_grid.attach_next(form_field)
                self._form_fields.append(form_field)
                form_field.show()
                form_field.show_all()
        self._update_form_from_default()
        self.show_all()
    
    def init_from_nothing(self):
        """ Remove form """
        print("DEBUG", "init from nothing")
        self._empty_form()
        self._record = None
        self._table = None
        self.show_all()

    def _on_button_save_clicked(self, button:Button):
        if not self._record:
            values = {form_field.Field:form_field.get_value() for form_field in self._form_fields}
            self._record = Record(self._table, values)
            self.db_handler.create_record_or_fail(self._record)
        else:
            self.db_handler.update_record_or_fail(self._record)

    def _on_button_cancel_clicked(self, button:Button):
        if self._record: self._update_form_from_record()
        elif self._table: self._update_form_from_default()
        else: pass

