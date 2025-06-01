from logging import LogRecord, Handler, getLogger

from gui.bricks.dialogs import InfoDialog


class DialogHandler(Handler):
    """ Wrapper of FileHandler to add an info popup, does not freeze the app """
    def emit(self, record:LogRecord) -> None:
        if record.exc_info:
            exc_type, value, _ = record.exc_info
            _ = InfoDialog(str(exc_type), value, freeze_app=False)

def setup_popup_logger() -> None:
    getLogger("global").addHandler(DialogHandler(level=30))
    # TODO this is warning level, where should that be parameterized?
