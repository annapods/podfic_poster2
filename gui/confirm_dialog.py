from typing import Callable, Tuple
from gi.repository.Gtk import Dialog as GtkDialog, STOCK_CANCEL, STOCK_OK, Label, Button
from gi.repository.Gtk import ResponseType, PositionType

from gui.base_graphics import ScrollWindow



class Dialog(GtkDialog):
    """ Parent class for all dialogs """
    
    OK = ResponseType.OK
    CANCEL = ResponseType.CANCEL

    def __init__(self, title:str, freeze_app:bool=False, parent=None):
        super().__init__(title=title, flags=0)
        content_area = self.get_content_area()
        self._box = ScrollWindow()
        content_area.add(self._box)
        self.show_all()
        self.set_transient_for(parent)
        self.set_modal(freeze_app)
        # self.hide() removes the dialog from view, however keeps it stored in memory
        # self.destroy()

class InfoDialog(Dialog):
    """ Popup with text and title, closes when OK is clicked """
    def __init__(
            self, title:str="FYI", text:str="Did you know...?",
            freeze_app:bool=False, parent=None):
        super().__init__(title=title, freeze_app=freeze_app, parent=parent)
        label = Label(label=text)
        self._box.add(label)

        button_ok = Button(label="OK")
        button_ok.connect("clicked", lambda x: self.destroy())
        self._box.add(button_ok)
        
        self.show_all()
        self.set_modal(freeze_app)


class ConfirmDialog(Dialog):
    """ """
    def __init__(
            self, title:str="Confirm?", text:str="Do you really want to do this?",
            freeze_app:bool=True, parent=None):
        super().__init__(title=title, freeze_app=freeze_app, parent=parent)
        self.add_button(STOCK_CANCEL, Dialog.CANCEL)
        self.add_button(STOCK_OK, Dialog.OK)
        self._box.add(Label(label=text))
        self.show_all()
