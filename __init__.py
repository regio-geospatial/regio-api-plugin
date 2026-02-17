# -*- coding: utf-8 -*-
def classFactory(iface):
    from .regio_api_plugin import RegioApiPlugin
    return RegioApiPlugin(iface)
