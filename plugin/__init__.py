from calibre.customize import InterfaceActionBase


class LastReadPlugin(InterfaceActionBase):
    name = 'Last Read'
    description = 'Keeps a "Last Read" date column current from the calibre viewer and sorts the library by it'
    author = 'defUserName-404'
    version = (1, 0, 0)
    minimum_calibre_version = (6, 0, 0)
    actual_plugin = 'calibre_plugins.last_read.ui:LastReadAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.last_read.config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
        ac = self.actual_plugin_
        if ac is not None:
            ac.apply_settings()
