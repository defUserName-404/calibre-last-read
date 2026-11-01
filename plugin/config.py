from qt.core import QCheckBox, QFormLayout, QWidget

from calibre.utils.config import JSONConfig

prefs = JSONConfig('plugins/last_read')
prefs.defaults['sort_enabled'] = True


def get_cfg() -> dict:
    return {k: prefs[k] for k in prefs.defaults}


class ConfigWidget(QWidget):
    def __init__(self):
        super().__init__()
        form = QFormLayout(self)
        self.sort = QCheckBox('Sort the library by Last Read (newest first) on startup and after each read')
        self.sort.setChecked(prefs['sort_enabled'])
        form.addRow(self.sort)

    def save_settings(self) -> None:
        prefs['sort_enabled'] = self.sort.isChecked()
