import distutils
import os
import subprocess

import setuptools
from setuptools.command.develop import develop
from setuptools.command.install import install


def build_js():
    subprocess.check_call(["yarn", "install"], cwd=os.path.join(os.getcwd(), "frontend"))
    subprocess.check_call(["yarn", "run", "build"], cwd=os.path.join(os.getcwd(), "frontend"))


# Build JS code when this package is installed in virtual env
# https://stackoverflow.com/a/36902139
class BuildJSDevelopCommand(develop):
    def run(self):
        self.announce("Building JS code", level=distutils.log.INFO)
        build_js()
        super().run()


class BuildJSInstallCommand(install):
    def run(self):
        self.announce("Building JS code", level=distutils.log.INFO)
        build_js()
        super().run()


setuptools.setup(
    name="simccs-maptool",
    version="0.0.1",
    description="SimCCS MapTool plugin to Airavata Django Portal",
    packages=setuptools.find_packages(),
    install_requires=[
        'django>=1.11.16',
        'cython',
        'pyjnius',
        'pyshp',
        "airavata-django-portal-sdk @ git+https://github.com/apache/airavata-django-portal-sdk.git@master#egg=airavata-django-portal-sdk",
        'djangorestframework',
        # Pandas 1.2 requires Python 3.7+ and our deployments are currently on Python 3.6
        'pandas<1.2',
        'geopandas'
    ],
    entry_points="""
[airavata.djangoapp]
simccs_maptool = simccs_maptool.apps:MapToolConfig
[airavata.output_view_providers]
cplex-solution-link = simccs_maptool.output_views:SolutionLinkProvider
""",
    cmdclass={
        'develop': BuildJSDevelopCommand,
        'install': BuildJSInstallCommand,
    }
)
