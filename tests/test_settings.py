

import os

BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "abc123"
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    "simccs_maptool.apps.MapToolConfig",
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASEDIR, 'db.sqlite3'),
    }
}
MAPTOOL_SETTINGS = {
    "CPLEX_APPLICATION_ID": "Cplex_a7eaf483-ab92-4441-baeb-2f302ccb2919",
    "DATASETS_DIR": os.path.join(BASEDIR, "simccs_maptool", "simccs", "Datasets")
}
