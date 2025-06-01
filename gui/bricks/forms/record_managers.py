from typing import Any, Dict, Tuple, Callable, List
from gi.repository.Gtk import Button, PositionType, Label, Button, PositionType, Align


from db.handler import SQLiteHandler
from db.objects import Field, Record, Table
from gui.bricks.containers import PaddedGrid
from gui.bricks.dialogs import ConfirmDialog, Dialog, InfoDialog
from gui.bricks.forms.form_fields import FormField, get_form_field
from gui.bricks.forms.ext_widgets import _select_ext_widget_type


class ExtFormField(FormField):
    """ Any form field that is a reference to another table 
    Several widgets available """

    def __init__(self, field:Field, *args, **kwargs):
        self._db_handler = SQLiteHandler()
        self.table = field.foreign_key_table
        self.last_record = None  # TODO default values
        self._widget = None
        super().__init__(field, *args, **kwargs)

        # Modify buttons
        modify_button = Button(label="?")
        modify_button.connect("clicked", self._on_button_modify_clicked)
        self.attach_next(modify_button, PositionType.RIGHT)

        # Create button
        create_button = Button(label="+")
        create_button.connect("clicked", self._on_button_create_clicked)
        self.attach_next(create_button, PositionType.RIGHT)

    def set_default(self) -> None:
        self._widget.set_value(self.field.default_value)
    
    def set_value(self, value:Record|None) -> None:
        self._widget.set_value(value)
    
    def get_value(self) -> Record|None:
        return self._widget.get_value()

    def _get_options_from_db(self) -> List[Record|None]:
        """ Fetch and return all records in the DB table of the field """
        options = self._db_handler.get_records(self.table)
        options.sort(
            key=lambda record: record.values[self.table.sort_rows_by],
            reverse=False)
        return options

    def _on_selection_modified(self) -> None:
        """ If selection changes, it needs to be traced/accessible """
        if self._widget:  # At widget init, the selection will be initialized before the widget reference is saved
            self.last_record = self._widget.get_value()

    def _init_widget(self) -> None:
        """ Initialize widget OR refresh to take into account for modification of DB records """
        # Get (new) list of options and type of widget
        self._options = self._get_options_from_db()
        include_none = not self.field.mandatory
        new_type = _select_ext_widget_type(len(self._options))
        
        # Resetting the widget will deselect and by doing so, update last_record
        last_record = self.last_record

        if not self._widget: # Init of the form, cf super.__init__                          
            self._widget = new_type(self._options, include_none, self._on_selection_modified)
        if type(self._widget) == new_type:  # Refresh but same widget type
            self._widget.load_options(self._options, include_none)
        
        else:  # Refresh and new widget type
            self.remove(self._widget)
            self._widget = new_type(self._options, include_none, self._on_selection_modified)
            self.attach(self._widget, 0, 0)
            self._format_widget()
            self._widget.show_all()
        
        # Depending on the case, select the previous selection, or the default value, or nothing
        if last_record: self._widget.set_value(last_record)
        else: self.set_default()

    def _on_button_modify_clicked(self, _:Button) -> None:
        """ Open a record manager dialog for the record selected 
        If none, for a new record """
        _ = RecordManagerDialog(
            table=self.table,
            record=self.last_record,
            on_change_notify=self._on_record_modified)

    def _on_button_create_clicked(self, _:Button) -> None:
        """ Open a record manager dialog for a new record """
        _ = RecordManagerDialog(
            table=self.table,
            record=None,
            on_change_notify=self._on_record_modified,
            delete_button=False)

    def _on_record_modified(self, record:Record) -> None:
        """ If a record manager dialog generated from this form modified a record, reload """
        self.last_record = record
        self._init_widget()


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
        # Label
        label_text = "*"+field.field_name if field.mandatory else field.field_name
        label = Label(label_text)
        label.set_halign(Align.END)
        # Form field
        if field.foreign_key_table: form_field = ExtFormField(field)
        else: form_field = get_form_field(field)
        # DEBUG size (note that label is no longer an attr of this class)
        # using width=N only work if set_column_homogeneous(True) on the grid
        # label.set_line_wrap(True)
        # label.set_size_request(150,-1)
        # form_field._widget.set_hexpand(True)
        # label.set_size_request(20,20)
        return label, form_field

    def reset_form_from_record(self, record:Record):
        """ Recreate all form fields and fill them with record values """
        self.reset_form_from_nothing()
        self.last_record = record
        self.last_table = record.parent_table

        for i, field in enumerate(record.parent_table.fields):
            label, form_field = self._get_form_field_and_label(field)
            self.attach(label, 0, i-1)
            self.attach(form_field, 1, i-1)
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
            init_table:Table=None, init_record:Record=None,
            on_change_notify:Callable=lambda x: None,
            on_cancel_notify:Callable=lambda x: None,
            delete_button:bool=True,
        ):
        super().__init__(init_table, init_record)
        self._on_change_notify = on_change_notify
        self._on_cancel_notify = on_cancel_notify

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
        try:
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
        except ValueError as e:
            self.error("Something went wrong while trying to save", exc_info=e)

    def _on_button_cancel_clicked(self, _:Button):
        if self.last_record: self.reset_form_from_record(self.last_record)
        elif self.last_table: self.reset_form_from_table(self.last_table)
        else: self.reset_form_from_nothing()
        self._on_cancel_notify()

    def _on_button_delete_clicked(self, _:Button):
        if self.last_record:
            popup = ConfirmDialog(self.last_record.display_name, freeze_app=True)
            response = popup.run()
            if response == Dialog.OK:
                self._db_handler.delete_record_or_fail(self.last_record)
                self.last_record = None
                self.reset_form_from_table(self.last_table)
                self._on_change_notify()
            # elif response == Dialog.CANCEL:
            #     pass
            popup.destroy()
        else:
            popup = InfoDialog("???", "No record to delete", freeze_app=False)
            # response = popup.run()
            # popup.destroy()
            

class RecordManagerDialog(Dialog):
    """ The RecordManagerGrid but in a popup """
    def __init__(self,
            table:Table, record:Record=None,
            on_change_notify:Callable=lambda x: None,
            delete_button:bool=True,
            self_destruct_after_call:bool=True):
        
        if record: title = f"Edit {record.parent_table.table_name} record"
        elif table: title = f"Create {table.table_name} record"
        else: title = "???"
        super().__init__(title, freeze_app=False, add_ok_button=False)

        def _on_change_notify() -> None:
            """ Wrapper to add table and record to callable"""
            if self_destruct_after_call:
                self.destroy()
            on_change_notify(record_manager.last_record)
        
        def _on_cancel_notify() -> None:
            if self_destruct_after_call:
                self.destroy()

        record_manager = RecordManagerGrid(
            init_table=table, init_record=record,
            on_change_notify=_on_change_notify,
            on_cancel_notify=_on_cancel_notify,
            delete_button=delete_button)

        self._box.add(record_manager)
        self.set_size_request(600,500)  #DEBUG size this one works but at what cost
        self.show_all()
