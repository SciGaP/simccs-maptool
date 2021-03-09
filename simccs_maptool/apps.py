import logging
import os

import jnius_config
from django.apps import AppConfig
from django.conf import settings

from simccs_maptool import datasets, simccs_helper

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Settings:
    WEBPACK_LOADER = {
        "SIMCCS_MAPTOOL": {
            "BUNDLE_DIR_NAME": "simccs_maptool/dist/",  # must end with slash
            "STATS_FILE": os.path.join(
                BASE_DIR,
                "static",
                "simccs_maptool",
                "dist",
                "webpack-stats.json",
            ),
        }
    }


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
    settings = Settings()
    nav = [
        {
            "label": "Map Tool",
            "icon": "fa fa-map",
            "url": "simccs_maptool:home",
            "active_prefixes": [""],
        },
        {
            "label": "Build",
            "icon": "fa fa-tools",
            "url": "simccs_maptool:projects",
            "active_prefixes": ["build/projects"],
        },
        {
            "label": "Documentation Links",
            "icon": "fa fa-question",
            "url": "simccs_maptool:help",
            "active_prefixes": ["help"],
        },
    ]

    def ready(self):
        logger.info("MapToolConfig.ready() called")
        init_pyjnius()
        try:
            # get path of Lower48US dataset and set it as a cached cost surface
            # on simccs_helper note: dataset may not exist, need to check
            lower48_dir = datasets.get_dataset_dir(datasets.LOWER48US_DATASET_ID)
            simccs_helper.register_cost_surface_data_cache(lower48_dir)
        except Exception as e:
            logger.warning("Unable to register Lower48US cost surface cache: " + str(e))


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
        jnius_config.add_options("-Djava.awt.headless=true")
        DEFAULT_JAVA_OPTIONS = ("-Xmx4g",)
        java_options = getattr(settings, "MAPTOOL_SETTINGS", {}).get(
            "JAVA_OPTIONS", DEFAULT_JAVA_OPTIONS
        )
        if isinstance(java_options, list) or isinstance(java_options, tuple):
            jnius_config.add_options(*java_options)
        else:
            jnius_config.add_options(java_options)
        jnius_config.set_classpath(
            os.path.join(BASE_DIR, "simccs", "lib", "SimCCS.jar"),
            os.path.join(BASE_DIR, "simccs", "lib", "maptool.jar"),
        )
        logger.info(
            "Initialized jnius with classpath={}, options={}".format(
                jnius_config.get_classpath(), jnius_config.get_options()
            )
        )
        import jnius  # noqa
