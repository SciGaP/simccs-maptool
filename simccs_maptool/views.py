# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import glob
import json
import logging
import os
import tempfile
from datetime import datetime

import shapefile
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import TemplateView

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_BASEPATH = os.path.join(BASEDIR, "simccs", "Datasets")
CASE_STUDIES_DIR = os.path.join(BASEDIR, "static", "Scenarios")
SOUTHEASTUS_DATASET_ID = "Southeast_US"

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cplex_application_id"] = getattr(settings, "MAPTOOL_SETTINGS", {}).get(
            "CPLEX_APPLICATION_ID", "Cplex_a7eaf483-ab92-4441-baeb-2f302ccb2919"
        )
        return context


class HomeView_test(TemplateView):
    template_name = "index_test.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cplex_application_id"] = getattr(settings, "MAPTOOL_SETTINGS", {}).get(
            "CPLEX_APPLICATION_ID", "Cplex_a7eaf483-ab92-4441-baeb-2f302ccb2919"
        )
        return context


class HelpView(TemplateView):
    template_name = "simccs_maptool/help.html"


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


@login_required
def generate_mps(request):

    # MPS model parameters
    capital_recovery_rate = float(request.GET.get("crf", "0.1"))
    num_years = float(request.GET.get("numYears", 10))
    capacity_target = float(request.GET.get("capacityTarget", 5))
    sources = request.GET.get("sources", None)
    sinks = request.GET.get("sinks", None)
    dataset = request.GET.get("dataset", SOUTHEASTUS_DATASET_ID)

    # TODO: provide Django apps with utility for writing to gateway data storage
    userdir = os.path.join(settings.GATEWAY_DATA_STORE_DIR, request.user.username)
    datasets_basepath = os.path.join(userdir, "Datasets")
    dataset_dir = os.path.join(datasets_basepath, dataset)
    os.makedirs(dataset_dir, exist_ok=True)
    # Symlink in the BaseData directory for the dataset
    basedata_dir = os.path.join(dataset_dir, "BaseData")
    if not os.path.exists(basedata_dir):
        os.symlink(_get_basedata_dir(dataset), basedata_dir)
    # Create a scenario directory
    scenarios_dir = os.path.join(dataset_dir, "Scenarios")
    os.makedirs(scenarios_dir, exist_ok=True)
    scenario_dir = os.path.join(
        scenarios_dir,
        "scenario_{}".format(datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")),
    )
    os.mkdir(scenario_dir)

    scenario = os.path.basename(scenario_dir)
    # Write Sources.txt
    os.mkdir(os.path.join(scenario_dir, "Sources"))
    with open(
        os.path.join(scenario_dir, "Sources", "Sources.txt"), mode="w"
    ) as sources_file:
        if sources is not None:
            sources_file.write(sources)
        else:
            sources_file.write(
                """ID	costFix ($M)	fixO&M ($M/y)	varO&M ($/tCO2)	capMax (MtCO2/y)	N/A	LON	LAT	NAME
1	2842.8	223.4	81.93	7.236	1	-88.0103	31.0069	1
2	3052.4	234.5	58	7.236	1	-86.4567	33.2442	2
3	407.9	52.5	106.78	0.297	1	-85.9708	34.0128	3
4	2108.5	192	71.9	4.635	1	-87.2003	33.6446	4
5	904.4	80.1	67.06	2.034	1	-87.7811	32.6017	5
6	3959	258.9	36.12	17.901	1	-87.0597	33.6319	6
7	1910.5	160.8	94.74	3.276	1	-87.2289	30.5661	7
8	539.6	62.9	88.11	1.26	1	-85.7003	30.2689	8
9	339.6	48.6	123.82	0.018	1	-84.8869	30.6689	9
10	4535	288.8	79.8	17.928	1	-84.9192	34.1256	10
11	1424	141.5	69.03	3.096	1	-85.3456	34.2533	11
12	2361	190.6	77.67	5.319	1	-83.2994	33.1942	12
13	834.4	78.4	83.98	1.782	1	-84.475	33.8244	13
14	474.6	73.3	93.05	1.026	1	-81.1458	32.1486	14
15	264.7	31.1	81.24	0.027	1	-84.1322	31.4444	15
16	5295	311.2	41.91	20.331	1	-83.8072	33.0583	16
17	2539	155.1	67.62	6.129	1	-85.0345	33.4124	17
18	2307.4	239.4	72.62	4.059	1	-84.8986	33.4622	18
19	1405.6	102.3	68.72	2.529	1	-89.0265	30.4408	19
20	2091	128.6	89.68	5.013	1	-88.5574	30.5335	20
"""
            )
    # Write Sinks.txt
    os.mkdir(os.path.join(scenario_dir, "Sinks"))
    with open(os.path.join(scenario_dir, "Sinks", "Sinks.txt"), mode="w") as sinks_file:
        if sinks is not None:
            sinks_file.write(sinks)
        else:
            sinks_file.write(
                """0	1	2	3	4	5	6	7	8	9	10	11	12	13	14	15	16
1	1	379	40.951	0.000	0.375	4.575	0.175	2.61	0	-91.2980	28.9920	0	0	0	0	Gulf offshore
2	2	379	40.951	0.000	0.375	4.575	0.175	2.61	0	-91.1764	31.5559	0	0	0	0	Cranfield
3	3	360	63.063	0.000	0.180	3.859	0.201	3.02	0	-88.5068	30.5078	0	0	0	0	Escatawpa
4	4	498	63.063	0.000	0.500	3.602	0.181	2.84	0	-88.2337	31.0930	0	0	0	0	Citronelle
5	5	480	18.178	0.000	0.500	4.204	0.191	2.74	0	-86.7961	30.7153	0	0	0	0	Disposal Area 1 (DA1)
6	6	549	63.063	0.000	0.600	3.017	0.154	2.83	0	-84.8449	30.6128	0	0	0	0	Disposal Area 2 (DA1b)
7	7	845	63.063	0.000	0.800	2.930	0.135	2.77	0	-81.6781	31.7306	0	0	0	0	Disposal Area 3 (DA2)
"""
            )
    # Write Linear.txt
    os.mkdir(os.path.join(scenario_dir, "Transport"))
    with open(
        os.path.join(scenario_dir, "Transport", "Linear.txt"), mode="w"
    ) as linear:
        linear.write(
            """ID	X (Con)	C (Con)	X (ROW)	C (ROW)
1	0.0762	0.1789	0.0069	0.1174
2	0.0162	0.4932	0.0009	0.1511
"""
        )

    try:
        from jnius import autoclass

        DataStorer = autoclass("simccs.dataStore.DataStorer")
        data = DataStorer(datasets_basepath, dataset, scenario)
        Solver = autoclass("simccs.solver.Solver")
        solver = Solver(data)
        data.setSolver(solver)
        MPSWriter = autoclass("simccs.solver.MPSWriter")
        os.mkdir(os.path.join(scenario_dir, "MIP"))
        MPSWriter.writeMPS(
            "mip.mps",
            data,
            capital_recovery_rate,
            num_years,
            capacity_target,
            datasets_basepath,
            dataset,
            scenario,
        )
    except Exception as e:
        logger.exception("Error occurred when calling writeMPS: " + str(e.stacktrace))
        raise

    mps_file_path = os.path.join(scenario_dir, "MIP", "mip.mps")
    rel_mps_file_path = os.path.relpath(mps_file_path, start=userdir)
    results_dir = os.path.join(scenario_dir, "Results")
    os.mkdir(results_dir)
    # symlink the mps file into this Results directory (makeShapeFiles expects
    # .mps and .sol files to be in the same directory)
    os.symlink(mps_file_path, os.path.join(results_dir, "mip.mps"))
    rel_results_dir = os.path.relpath(results_dir, start=userdir)
    return JsonResponse(
        {"user_file": rel_mps_file_path, "results_dir": rel_results_dir}
    )


@login_required
def experiment_result(request, experiment_id):
    """
    Return a JSON object with nested GeoJSON objects.
    {
        "Network": GeoJSON,
        "Sinks":   GeoJSON,
        "Sources": GeoJSON
    }
    """
    results_dir = _get_results_dir(request, experiment_id)
    # figure out the scenario directory
    shapefiles_dir = os.path.join(results_dir, "shapeFiles")
    geojson_dir = os.path.join(results_dir, "geojson")
    if not os.path.exists(shapefiles_dir):
        _create_shapefiles_for_result(request, results_dir)
    if not os.path.exists(geojson_dir):
        _create_geojson_for_result(request, results_dir)
    with open(
        os.path.join(results_dir, "geojson", "Network.geojson")
    ) as network_geojson, open(
        os.path.join(results_dir, "geojson", "Sources.geojson")
    ) as sources_geojson, open(
        os.path.join(results_dir, "geojson", "Sinks.geojson")
    ) as sinks_geojson:
        return JsonResponse(
            {
                "Network": json.load(network_geojson),
                "Sources": json.load(sources_geojson),
                "Sinks": json.load(sinks_geojson),
            }
        )


@login_required
def solution_summary(request, experiment_id):
    results_dir = _get_results_dir(request, experiment_id)
    solution = _load_solution(request, results_dir)
    return JsonResponse(
        {
            "numOpenedSources": solution.numOpenedSources,
            "numOpenedSinks": solution.numOpenedSinks,
            "targetCaptureAmount": solution.targetCaptureAmount,
            "numEdgesOpened": solution.numEdgesOpened,
            "projectLength": solution.projectLength,
            "totalCaptureCost": solution.totalCaptureCost,
            "unitCaptureCost": solution.unitCaptureCost,
            "totalTransportCost": solution.totalTransportCost,
            "unitTransportCost": solution.unitTransportCost,
            "totalStorageCost": solution.totalStorageCost,
            "unitStorageCost": solution.unitStorageCost,
            "totalCost": solution.totalCost,
            "unitTotalCost": solution.unitTotalCost,
            "crf": solution.getCRF(),
        }
    )


def _get_results_dir(request, experiment_id):
    experiment = request.airavata_client.getExperiment(
        request.authz_token, experiment_id
    )
    # Get the experimentDataDir which is the Results/ directory
    return experiment.userConfigurationData.experimentDataDir


def _create_shapefiles_for_result(request, results_dir):
    userdir = os.path.join(settings.GATEWAY_DATA_STORE_DIR, request.user.username)
    datasets_basepath = os.path.join(userdir, "Datasets")
    scenario_dir = os.path.dirname(results_dir)
    scenario = os.path.basename(scenario_dir)
    dataset = _get_dataset_from_results_dir(results_dir)
    try:
        from jnius import autoclass

        # initialize the Solver/DataStorer
        DataStorer = autoclass("simccs.dataStore.DataStorer")
        data = DataStorer(datasets_basepath, dataset, scenario)
        Solver = autoclass("simccs.solver.Solver")
        solver = Solver(data)
        data.setSolver(solver)
        logger.debug("Scenario data loaded for {}".format(scenario_dir))
        # load the .mps/.sol solution
        solution = data.loadSolution(results_dir)
        logger.debug("Solution loaded from {}".format(results_dir))
        # generate shapefiles
        data.makeShapeFiles(results_dir, solution)
        logger.debug(
            "Shape files created in {}".format(os.path.join(results_dir, "shapeFiles"))
        )
    except Exception as e:
        logger.exception(
            "Error occurred when calling makeShapeFiles: " + str(e.stacktrace)
        )
        raise


def _load_solution(request, results_dir):
    userdir = os.path.join(settings.GATEWAY_DATA_STORE_DIR, request.user.username)
    datasets_basepath = os.path.join(userdir, "Datasets")
    scenario_dir = os.path.dirname(results_dir)
    scenario = os.path.basename(scenario_dir)
    dataset = _get_dataset_from_results_dir(results_dir)
    try:
        from jnius import autoclass

        # initialize the Solver/DataStorer
        DataStorer = autoclass("simccs.dataStore.DataStorer")
        data = DataStorer(datasets_basepath, dataset, scenario)
        Solver = autoclass("simccs.solver.Solver")
        solver = Solver(data)
        data.setSolver(solver)
        logger.debug("Scenario data loaded for {}".format(scenario_dir))
        # load the .mps/.sol solution
        solution = data.loadSolution(results_dir)
        logger.debug("Solution loaded from {}".format(results_dir))
        return solution
    except Exception as e:
        logger.exception("Error occurred when loading solution: " + str(e.stacktrace))
        raise


def _create_geojson_for_result(request, results_dir):
    network_sf = shapefile.Reader(os.path.join(results_dir, "shapeFiles", "Network"))
    sinks_sf = shapefile.Reader(os.path.join(results_dir, "shapeFiles", "Sinks"))
    sources_sf = shapefile.Reader(os.path.join(results_dir, "shapeFiles", "Sources"))
    geojson_dir = os.path.join(results_dir, "geojson")
    os.mkdir(geojson_dir)
    with open(os.path.join(geojson_dir, "Network.geojson"), "w") as network_geojson_f:
        _write_shapefile_to_geojson(network_sf, network_geojson_f)
    with open(os.path.join(geojson_dir, "Sinks.geojson"), "w") as sinks_geojson_f:
        _write_shapefile_to_geojson(sinks_sf, sinks_geojson_f)
    with open(os.path.join(geojson_dir, "Sources.geojson"), "w") as sources_geojson_f:
        _write_shapefile_to_geojson(sources_sf, sources_geojson_f)


def _write_shapefile_to_geojson(shapefile, geojson_f):
    # From http://geospatialpython.com/2013/07/shapefile-to-geojson.html
    fields = shapefile.fields[1:]
    field_names = [field[0] for field in fields]
    buffer = []
    for sr in shapefile.shapeRecords():
        atr = dict(zip(field_names, sr.record))
        geom = sr.shape.__geo_interface__
        buffer.append(dict(type="Feature", geometry=geom, properties=atr))

    # write the GeoJSON file
    geojson_f.write(
        json.dumps({"type": "FeatureCollection", "features": buffer}, indent=2) + "\n"
    )


def _get_dataset_from_results_dir(results_dir):
    scenario_dir = os.path.dirname(results_dir)
    dataset_dir = os.path.dirname(os.path.dirname(scenario_dir))
    return os.path.basename(dataset_dir)


def candidate_network(request):

    sources = request.GET.get("sources", None)
    sinks = request.GET.get("sinks", None)
    dataset = request.GET.get("dataset", SOUTHEASTUS_DATASET_ID)

    with tempfile.TemporaryDirectory() as datasets_basepath:
        dataset_dir = os.path.join(datasets_basepath, dataset)
        os.makedirs(dataset_dir, exist_ok=True)
        # Symlink in the BaseData directory for the dataset
        basedata_dir = os.path.join(dataset_dir, "BaseData")
        if not os.path.exists(basedata_dir):
            os.symlink(_get_basedata_dir(dataset), basedata_dir)
        # Create a scenario directory
        scenarios_dir = os.path.join(dataset_dir, "Scenarios")
        os.makedirs(scenarios_dir, exist_ok=True)
        scenario_dir = os.path.join(
            scenarios_dir,
            "scenario_{}".format(datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")),
        )
        os.mkdir(scenario_dir)

        scenario = os.path.basename(scenario_dir)
        # Write Sources.txt
        os.mkdir(os.path.join(scenario_dir, "Sources"))
        with open(
            os.path.join(scenario_dir, "Sources", "Sources.txt"), mode="w"
        ) as sources_file:
            sources_file.write(sources)
        # Write Sinks.txt
        os.mkdir(os.path.join(scenario_dir, "Sinks"))
        with open(
            os.path.join(scenario_dir, "Sinks", "Sinks.txt"), mode="w"
        ) as sinks_file:
            sinks_file.write(sinks)
        # Write Linear.txt
        os.mkdir(os.path.join(scenario_dir, "Transport"))
        with open(
            os.path.join(scenario_dir, "Transport", "Linear.txt"), mode="w"
        ) as linear:
            linear.write(
                """ID	X (Con)	C (Con)	X (ROW)	C (ROW)
1	0.0762	0.1789	0.0069	0.1174
2	0.0162	0.4932	0.0009	0.1511
"""
            )

        try:
            # Run the Solver to generate candidate graph
            from jnius import autoclass

            DataStorer = autoclass("simccs.dataStore.DataStorer")
            data = DataStorer(datasets_basepath, dataset, scenario)
            Solver = autoclass("simccs.solver.Solver")
            solver = Solver(data)
            data.setSolver(solver)
            data.makeCandidateNetworkShapeFiles()
            results_dir = os.path.join(scenario_dir, "Network", "CandidateNetwork")
            _create_geojson_for_result(request, results_dir)
            with open(
                os.path.join(results_dir, "geojson", "Network.geojson")
            ) as network_geojson, open(
                os.path.join(results_dir, "geojson", "Sources.geojson")
            ) as sources_geojson, open(
                os.path.join(results_dir, "geojson", "Sinks.geojson")
            ) as sinks_geojson:
                return JsonResponse(
                    {
                        "Network": json.load(network_geojson),
                        "Sources": json.load(sources_geojson),
                        "Sinks": json.load(sinks_geojson),
                    }
                )
        except Exception as e:
            logger.exception(
                "Error occurred when loading solution: " + str(e.stacktrace)
            )
            raise


def _get_basedata_dir(dataset):

    dataset_dirname = _get_dataset_dirname(dataset)
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
    raise Exception("Unable to find basedata directory for dataset {}".format(dataset))


def _get_dataset_dirname(dataset):
    for summary_json_path in glob.glob(
        os.path.join(CASE_STUDIES_DIR, "*", "summary.json")
    ):
        with open(summary_json_path) as f:
            summary_json = json.load(f)
            if summary_json["dataset-id"] == dataset:
                return summary_json["dataset-dirname"]
    raise Exception("Unrecognized dataset: {}".format(dataset))
