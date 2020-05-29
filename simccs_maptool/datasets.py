import logging
import os

from django.conf import settings
import glob
import json

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_BASEPATH = os.path.join(BASEDIR, "simccs", "Datasets")
CASE_STUDIES_DIR = os.path.join(BASEDIR, "static", "Scenarios")
DATASETS_METADATA_DIR = os.path.join(BASEDIR, "static", "Datasets")
# Dataset IDs
LOWER48US_DATASET_ID = "Lower48US"

logger = logging.getLogger(__name__)


def get_basedata_dir(dataset_id):

    dataset_dirname = _get_dataset_dirname(dataset_id)
    if "DATASETS_DIR" in getattr(settings, "MAPTOOL_SETTINGS", {}):
        datasets_basepath = settings.MAPTOOL_SETTINGS["DATASETS_DIR"]
        basedata_dir = os.path.join(datasets_basepath, dataset_dirname, "BaseData")
        if os.path.exists(basedata_dir):
            return basedata_dir
    else:
        logger.warning("Setting MAPTOOL_SETTINGS['DATASETS_DIR'] is not defined")
    # For backwards compatibility, allow loading BaseData from within this repo
    # (SoutheastUS only)
    basedata_dir = os.path.join(DATASETS_BASEPATH, dataset_dirname, "BaseData")
    if os.path.exists(basedata_dir):
        return basedata_dir
    raise Exception(
        "Unable to find basedata directory for dataset {}".format(dataset_id)
    )


def _get_dataset_dirname(dataset):
    # Check for case studies specific datasets
    for summary_json_path in glob.glob(
        os.path.join(CASE_STUDIES_DIR, "*", "summary.json")
    ):
        with open(summary_json_path, encoding="utf-8") as f:
            summary_json = json.load(f)
            if summary_json["dataset-id"] == dataset:
                return summary_json["dataset-dirname"]
    # Check for global datasets
    for summary_json_path in glob.glob(
        os.path.join(DATASETS_METADATA_DIR, "*", "summary.json")
    ):
        with open(summary_json_path, encoding="utf-8") as f:
            summary_json = json.load(f)
            if summary_json["dataset-id"] == dataset:
                return summary_json["dataset-dirname"]
    raise Exception("Unrecognized dataset: {}".format(dataset))
