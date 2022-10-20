"""simulation_demo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include
from django.contrib.auth.decorators import login_required
from django.urls import re_path
from rest_framework import routers

from . import geoserver, views

router = routers.DefaultRouter()
router.register(r"cases", views.CaseViewSet, basename="case")
router.register(r"datasets", views.DatasetViewSet, basename="dataset")
router.register(r"projects", views.SimccsProjectViewSet, basename="simccs-project")
router.register(r"workspaces", views.WorkspaceViewSet, basename="workspace")
router.register(r"notes", views.ScenarioExperimentNoteViewSet, basename="note")

app_name = "simccs_maptool"
urlpatterns = [
    re_path(r"^$", views.HomeView.as_view(), name="home"),
    re_path(r"^help/$", views.HelpView.as_view(), name="help"),
    re_path(r"^candidate-network/$", views.candidate_network, name="candidate-network"),
    re_path(r"^mps/$", views.generate_mps, name="generate-mps"),
    re_path(r"^experiment-result/(?P<experiment_id>[^/]+)$",
            views.experiment_result, name="experiment-result"),
    re_path(r"^solution-summary/(?P<experiment_id>[^/]+)$",
            views.solution_summary, name="solution-summary"),
    re_path(r"^build/projects/", views.ProjectsView.as_view(), name="projects"),
    re_path(r"^get-data", geoserver.get_data),
    re_path(r"^api/", include(router.urls)),
    re_path(r"^build$", login_required(views.BuildView.as_view()), name="build"),
    # for local debug:
    #url(r"^build", views.BuildView.as_view(), name="build"),
    
]
