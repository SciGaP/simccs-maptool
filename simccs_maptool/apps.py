from django.apps import AppConfig


class MapToolConfig(AppConfig):
    name = 'simccs_maptool'
    label = 'simccs_maptool'
    verbose_name = 'Map Tool'
    url_prefix = 'maptool'
    url_app_name = label
    app_order = 20
    url_home = url_app_name + ':home'
    fa_icon_class = 'fa-map'
    app_description = """
        SimCCS Map Tool.
    """
