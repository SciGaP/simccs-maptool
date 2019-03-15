import setuptools

setuptools.setup(
    name="simccs-maptool",
    version="0.0.1",
    description="SimCCS MapTool plugin to Airavata Django Portal",
    packages=setuptools.find_packages(),
    install_requires=[
        'django>=1.11.16'
    ],
    entry_points="""
[airavata.djangoapp]
simccs_maptool = simccs_maptool.apps:MapToolConfig
""",
)
