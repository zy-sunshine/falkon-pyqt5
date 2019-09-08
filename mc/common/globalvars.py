from mc.common.designutil import cached_property

class GlobalVar(object):

    @cached_property
    def app(self):
        from mc.app.MainApplication import MainApplication
        return MainApplication.instance()

    @cached_property
    def qzSettings(self):
        from mc.other.QzSettings import QzSettings
        return QzSettings.instance()

    @cached_property
    def appTools(self):
        from mc.tools.AppTools import AppTools
        return AppTools.instance()

    @cached_property
    def webScrollBarManager(self):
        from mc.tools.WebScrollBarManager import WebScrollBarManager
        return WebScrollBarManager()

    @cached_property
    def appSettings(self):
        from mc.other.AppSettings import AppSettings
        return AppSettings()

gVar = GlobalVar()
