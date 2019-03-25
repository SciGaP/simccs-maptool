import logging
import os

import jnius_config
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class MapToolConfig(AppConfig):
    name = "simccs_maptool"
    label = "simccs_maptool"
    verbose_name = "Map Tool"
    url_prefix = "maptool"
    url_app_name = label
    app_order = 20
    url_home = url_app_name + ":home"
    fa_icon_class = "fa-map"
    app_description = """
        SimCCS Map Tool.
    """

    def ready(self):
        logger.info("MapToolConfig.ready() called")
        init_pyjnius()


def init_pyjnius():
    if not jnius_config.vm_running:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        jnius_config.set_classpath(
            os.path.join(BASE_DIR, "simccs", "lib", "SimCCS.jar"),
            os.path.join(BASE_DIR, "simccs", "lib", "openmap.jar"),
        )
        logger.info(
            "Initialized jnius with classpath={}".format(jnius_config.get_classpath())
        )
        import jnius  # noqa
