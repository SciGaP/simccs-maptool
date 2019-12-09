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
from django.conf.urls import url

from . import views

app_name = "simccs_maptool"
urlpatterns = [
    url(r"^$", views.HomeView.as_view(), name="home"),
    url(r"^help/$", views.HelpView.as_view(), name="help"),
    url(r"^candidate-network/$", views.candidate_network, name="candidate-network"),
    url(r"^mps/$", views.generate_mps, name="generate-mps"),
    url(r"^experiment-result/(?P<experiment_id>[^/]+)$", views.experiment_result),
    url(r"^solution-summary/(?P<experiment_id>[^/]+)$", views.solution_summary),
]
