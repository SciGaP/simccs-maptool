# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.http import JsonResponse
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "index.html"


def simccs(request):
    # Important to only import jnius just before using it so that the classpath
    # can be configured before the VM starts. See apps.init_pyjnius
    from jnius import autoclass

    basepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "simccs", "Datasets"
    )
    dataset = "SoutheastUS"
    scenario = "scenario1"
    DataStorer = autoclass("simccs.dataStore.DataStorer")
    data = DataStorer(basepath, dataset, scenario)
    Solver = autoclass("simccs.solver.Solver")
    solver = Solver(data)
    data.setSolver(solver)

    return JsonResponse({"shortestPathEdges": data.getShortestPathEdges()})
