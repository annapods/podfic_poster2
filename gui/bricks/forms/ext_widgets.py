from typing import Any, Callable, List
from gi.repository.Gtk import Label, ComboBoxText, RadioButton

from db.objects import Record
from gui.bricks.containers import PlainGrid
from gui.bricks.tables import SingleSelectTable


def find_index_of(to_find:Record|str|None, in_list:List[Record|None]) -> int|None:
    """ Return the index of a record (or display name) in a list of records
    If not found, return None; if several, return the first one """

    # Comparison fonction depends on type of input
    def is_same(a:Record|str|None, b:List[Record|None]) -> bool:
        if b is None or b == "": return a == "" or a == None
        elif type(a) is str: return a == b.display_name
        elif type(a) is Record: return a == b
        
    # Return the index of the first match found
    for i, potential_match in enumerate(in_list):
        if is_same(to_find, potential_match):
            return i
        
    # # If none
    # self.debug(f"Couldn't find record {to_find} of type {type(to_find)}."+\
    #     f"Options are: {in_list}")
    return


def _select_ext_widget_type(number_options) -> type:
    """ Return the class of widget appropriate for this number of options """
    if number_options == 0: return NAExtWidget
    if number_options < 5: return RadioExtWidget
    if number_options < 10: return DropdownExtWidget
    return TableExtWidget


class ExtWidget:
    """ Abstract class """
    def set_value(self, value:Any|None) -> None:
        raise NotImplementedError
    def get_value(self) -> Record|None:
        raise NotImplementedError
    def load_options(self, options:List[Record|None], include_none:bool) -> None:
        raise NotImplementedError


class NAExtWidget(Label, ExtWidget):
    """ An external form field widget with no options available """
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.set_label("No options available")
    def set_value(self, value:Any|None) -> None: pass
    def get_value(self) -> Record|None: return None
    def load_options(self, options:List[Record|None], include_none:bool) -> None: pass


class RadioExtWidget(PlainGrid, ExtWidget):
    """ An external form field widget with radio button options
    https://stackoverflow.com/questions/391237/pygtk-radio-button """
    def __init__(self, options:List[Record], include_none:bool, on_selection_modified:Callable):
        super().__init__()
        self._buttons = []
        self._on_selection_modified = lambda x: on_selection_modified()
        self.load_options(options, include_none)

    def load_options(self, options:List[Record|None], include_none) -> None:
        self._options = options
        # Clean up
        for button in self._buttons: self.remove(button)
        # button.destroy()
        self._buttons = []
        # No options case
        if len(self._options) == 0: return
        # None option
        # If the field is not mandatory, none should be an option
        # If there is no default option, it will be the default
        # If there is no default option, no specific button should be selected
        # However, it's not possible to uncheck all radio buttons
        # Workaround: a hidden (or not) empty button for None
        # Source: https://stackoverflow.com/questions/1774161/is-there-a-way-to-uncheck-all-radio-buttons-in-a-group-pygtk
        # Combined with force-hiding it to avoid the refresh of the form by show_all
        # Source: https://github.com/JuliaGraphics/Gtk.jl/issues/609#issuecomment-1013753722
        none_button = RadioButton.new_with_label(None, "")
        self._options = [None]+self._options
        if not include_none:
            none_button.hide()
            none_button.set_no_show_all(True)
        self.attach(none_button)

        for option in self._options[1:]:
            button = RadioButton.new_with_label_from_widget(none_button, option.display_name)
            self.attach_next(button)
            button.show()
        self._buttons = list(reversed(none_button.get_group()))

        for button in self._buttons:
            button.connect("clicked", self._on_selection_modified)

    def set_value(self, value:Record|None):
        if not value:
            row = 0
        else:
            row = find_index_of(value, self._options)
            if not row: row = 0
        self._buttons[row].set_active(True)

    def get_value(self) -> Record|None:
        active_radios = [i for i, radio in enumerate(self._buttons) if radio.get_active()]
        # if not active_radios: return None
        return self._options[active_radios[0]]
        


class DropdownExtWidget(ComboBoxText, ExtWidget):
    """ An external form field widget with a dropdown menu """

    def __init__(self, options:List[Record|None], include_none:bool, on_selection_modified:Callable):
        super().__init__()
        self.load_options(options, include_none)
        self.connect("changed", lambda x: on_selection_modified())
        # DEBUG size this one is variable and changes the size of the scrollwindows

    def load_options(self, options:List[Record|None], include_none:bool) -> None:
        self.remove_all()
        # None option
        # If the field is not mandatory, none should be an option -> OK
        # If it is mandatory, it shouldn't be an option, but (unless there's a default value) no specific option should be selected -> KO
        # can't have both
        self._options = [None]+options
        for i, option in enumerate(self._options):
            self.insert(i, str(i), option.display_name if type(option) is Record else "")
        # self.show()

    def set_value(self, value:Record|None):
        if not value: row = 0
        else:
            row = find_index_of(value, self._options)
            if not row: row = 0
        self.set_active(row)

    def get_value(self) -> Record|None:
        text = self.get_active_text()
        row = find_index_of(text, self._options)
        if row: return self._options[row]
        


class TableExtWidget(SingleSelectTable, ExtWidget):
    """ A table form field widget with single selection and a button to edit records """
    
    def __init__(self, options:List[Record|None], include_none:bool, on_selection_modified:Callable):
        super().__init__(on_selection_modified)
        self.load_options(options, include_none)
        
    def load_options(self, options:List[Record|None], include_none:bool):
        """ Table widgets can't display an empty line, None is just unselecting all """
        SingleSelectTable.load_options(self, options)
    
    def set_value(self, value:Record|None) -> None:
        self.set_selected(value)

    def get_value(self) -> Record:
        return self.current_selection
    
        