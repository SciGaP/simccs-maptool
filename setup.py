import distutils
import logging
import os
import subprocess

import setuptools


def build_js():
    subprocess.check_call(["yarn", "install"],
                          cwd=os.path.join(os.getcwd(), "frontend"))
    subprocess.check_call(["yarn", "run", "build"],
                          cwd=os.path.join(os.getcwd(), "frontend"))


try:
    from setuptools.command.build import build as _build
    from setuptools.command.editable_wheel import \
        editable_wheel as _editable_wheel

    class build(_build):
        def run(self) -> None:
            self.announce("Building JS code", level=logging.INFO)
            build_js()
            super().run()

    class editable_wheel(_editable_wheel):
        def run(self) -> None:
            self.announce("Building JS code", level=logging.INFO)
            build_js()
            super().run()

    cmdclass = dict(build=build, editable_wheel=editable_wheel)

except ImportError:

    # For older versions of setuptools (Python 3.6)
    from setuptools.command.develop import develop as _develop
    from setuptools.command.install import install as _install

    # Build JS code when this package is installed in virtual env
    # https://stackoverflow.com/a/36902139

    class develop(_develop):
        def run(self):
            self.announce("Building JS code", level=distutils.log.INFO)
            build_js()
            super().run()

    class install(_install):
        def run(self):
            self.announce("Building JS code", level=distutils.log.INFO)
            build_js()
            super().run()

    cmdclass = dict(develop=develop, install=install)

setuptools.setup(cmdclass=cmdclass)
