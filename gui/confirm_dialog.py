from typing import Callable, Tuple
from gi.repository.Gtk import Dialog as GtkDialog, STOCK_CANCEL, STOCK_OK, Label, Button
from gi.repository.Gtk import ResponseType, PositionType



class Dialog(GtkDialog):
    OK = ResponseType.OK
    CANCEL = ResponseType.CANCEL
    def __init__(self, title:str, freeze_app:bool=False):  # TODO DEBUG freeze_app, always freezes
        super().__init__(title=title, flags=0)
        self._box = self.get_content_area()
        if freeze_app: self.set_modal(True)
        self.set_default_size(150, 100)
    # self.set_modal
    # self.hide() removes the dialog from view, however keeps it stored in memory
    # self.destroy()

class InfoDialog(Dialog):
    def __init__(self, title:str="FYI", text:str="Did you know...?", freeze_app=False):
        super().__init__(title=title, freeze_app=freeze_app)
        self.add_buttons(STOCK_OK, Dialog.ok)
        label = Label(label=text)
        self._box.add(label)
        self.show_all()

class ConfirmDialog(Dialog):
    cancel = ResponseType.CANCEL
    def __init__(
            self, title:str="Confirm?",
            text:str="Do you really want to do this?", freeze_app=True):
        super().__init__(title=title, freeze_app=freeze_app)
        self.add_button(STOCK_CANCEL, Dialog.CANCEL)
        self.add_button(STOCK_OK, Dialog.OK)
        self._box.add(Label(label=text))
        self.show_all()


# button = Button(label="Open dialog")
# button.connect("clicked", self.on_button_clicked)
# self.add(button)

# def on_button_clicked(self, widget):
#     dialog = ConfirmDialog(self)
#     response = dialog.run()
#     if response == ResOK:
#         print("The OK button was clicked")
#     elif response == ResCANCEL:
#         print("The Cancel button was clicked")
#     dialog.destroy()
