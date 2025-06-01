from typing import Callable, Tuple
from gi.repository.Gtk import Dialog as GtkDialog
from gi.repository.Gtk import Label, Button
from gi.repository.Gtk import ResponseType, PositionType

from gui.bricks.containers import PaddedGrid, ScrollWindow



class Dialog(GtkDialog):
    """ Parent class for all dialogs """
    
    OK = ResponseType.OK
    CANCEL = ResponseType.CANCEL

    def __init__(self, title:str, freeze_app:bool=False, parent=None, add_ok_button:bool=True):
        super().__init__(title=title, flags=0)
        content_area = self.get_content_area()
        self._box = ScrollWindow()
        content_area.add(self._box)
        self.show_all()
        self.set_transient_for(parent)
        self.set_modal(freeze_app)  # DEBUG to test 

        # OK button
        if add_ok_button:
            ok_button = self.add_button("OK", Dialog.OK)
            ok_button.connect("clicked", self._on_button_ok_clicked)
    
    def _on_button_ok_clicked(self, _:Button):
        self.destroy()
        # self.hide() removes the dialog from view, however keeps it stored in memory
        # self.destroy()

class InfoDialog(Dialog):
    """ Popup with text and title, closes when OK is clicked """
    def __init__(
            self, title:str="FYI", text:str="Did you know...?",
            freeze_app:bool=False, parent=None):
        super().__init__(title=title, freeze_app=freeze_app, parent=parent, add_ok_button=True)
        label = Label(text)
        label.set_wrap = True
        self._box.add(label)
        self.show_all()

class ConfirmDialog(Dialog):
    """ """
    def __init__(
            self, title:str="Confirm?", text:str="Do you really want to do this?",
            freeze_app:bool=True, parent=None):
        super().__init__(title=title, freeze_app=freeze_app, parent=parent, add_ok_button=True)
        self.add_button("Cancel", Dialog.CANCEL)
        self._box.add(Label(label=text))
        self.show_all()
