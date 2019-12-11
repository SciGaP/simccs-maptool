import logging
import os

import jnius_config
from django.apps import AppConfig
from django.conf import settings

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
    nav = [
        {
            'label': 'Map Tool',
            'icon': 'fa fa-map',
            'url': 'simccs_maptool:home',
            'active_prefixes': [''],
        },
        {
            'label': 'Documentation Links',
            'icon': 'fa fa-question',
            'url': 'simccs_maptool:help',
            'active_prefixes': ['help'],
        },
    ]

    def ready(self):
        logger.info("MapToolConfig.ready() called")
        init_pyjnius()


def init_pyjnius():
    if not jnius_config.vm_running:
        if "JAVA_HOME" not in os.environ:
            logger.info(
                "'JAVA_HOME' environment variable missing, "
                "trying to get from settings.py"
            )
            os.environ["JAVA_HOME"] = settings.JAVA_HOME
        logger.info("JAVA_HOME set to '{}'".format(os.environ["JAVA_HOME"]))
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        jnius_config.add_options('-Djava.awt.headless=true')
        jnius_config.add_options('-Xmx1536m')
        jnius_config.set_classpath(
            os.path.join(
                BASE_DIR, "simccs", "lib", "SimCCS.jar"
            )
        )
        logger.info(
            "Initialized jnius with classpath={}".format(jnius_config.get_classpath())
        )
        import jnius  # noqa
