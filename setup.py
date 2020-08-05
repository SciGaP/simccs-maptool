import setuptools

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
        "airavata-django-portal-sdk @ git+https://github.com/machristie/airavata-django-portal-sdk.git@master#egg=airavata-django-portal-sdk",
    ],
    entry_points="""
[airavata.djangoapp]
simccs_maptool = simccs_maptool.apps:MapToolConfig
[airavata.output_view_providers]
cplex-solution-link = simccs_maptool.output_views:SolutionLinkProvider
""",
)
