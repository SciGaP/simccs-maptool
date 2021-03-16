# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import glob
import json
import logging
import os
import tempfile
from contextlib import ContextDecorator
from threading import BoundedSemaphore
from urllib.parse import urlencode

import shapefile
from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView
from rest_framework import parsers, permissions, viewsets
from rest_framework.decorators import action

from simccs_maptool import datasets, models, serializers

from . import simccs_helper
from django.contrib.auth import get_user_model
from rest_framework.response import Response

# TODO: temporary code to allow working in develop and master branch of
# airavata-django-portal
if apps.is_installed("airavata_django_portal_sdk"):
    from airavata_django_portal_sdk import user_storage
else:
    from . import django_airavata_sdk as user_storage


BASEDIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_BASEPATH = os.path.join(BASEDIR, "simccs", "Datasets")
CASE_STUDIES_DIR = os.path.join(BASEDIR, "static", "Scenarios")
DATASETS_METADATA_DIR = os.path.join(BASEDIR, "static", "Datasets")
SOUTHEASTUS_DATASET_ID = "Southeast_US_2012"
LOWER48US_DATASET_ID = "Lower48US"
CACHED_LOWER48US_COST_SURFACE_DATA = None

logger = logging.getLogger(__name__)


class MaxConcurrentJavaCalls(BoundedSemaphore, ContextDecorator):
    pass


# Only allow MAX_CONCURRENT_JAVA_CALLS concurrent calls into Java code, since
# the Java code requires a substantial amount of memory. Any views that call
# into Java code should have this decorator applied to them.
max_concurrent_java_calls = MaxConcurrentJavaCalls(
    getattr(settings, "MAX_CONCURRENT_JAVA_CALLS", 1)
)


class HomeView(TemplateView):
    template_name = "simccs_maptool/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cplex_application_id"] = getattr(settings, "MAPTOOL_SETTINGS", {}).get(
            "CPLEX_APPLICATION_ID", "Cplex_a7eaf483-ab92-4441-baeb-2f302ccb2919"
        )
        context["cplex_hostname"] = getattr(settings, "MAPTOOL_SETTINGS", {}).get(
            "CPLEX_HOSTNAME", "bigred3.uits.iu.edu"
        )
        return context


class HelpView(TemplateView):
    template_name = "simccs_maptool/help.html"


class BuildView(TemplateView):
    template_name = "simccs_maptool/build.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cplex_application_id"] = getattr(settings, "MAPTOOL_SETTINGS", {}).get(
            "CPLEX_APPLICATION_ID", "Cplex_a7eaf483-ab92-4441-baeb-2f302ccb2919"
        )
        context["cplex_hostname"] = getattr(settings, "MAPTOOL_SETTINGS", {}).get(
            "CPLEX_HOSTNAME", "bigred3.uits.iu.edu"
        )
        return context


class ProjectsView(LoginRequiredMixin, TemplateView):

    template_name = "simccs_maptool/vue-app.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bundle_name'] = 'projects'
        return context


@login_required
@max_concurrent_java_calls
def generate_mps(request):

    # MPS model parameters
    capital_recovery_rate = float(request.POST.get("crf", "0.1"))
    num_years = float(request.POST.get("numYears", 10))
    capacity_target = float(request.POST.get("capacityTarget", 5))
    sources = request.POST["sources"]
    sinks = request.POST["sinks"]
    dataset_id = request.POST["dataset"]
    candidate_network = request.POST.get("candidateNetwork", None)

    with tempfile.TemporaryDirectory() as datasets_basepath:
        dataset_dir = datasets.get_dataset_dir(dataset_id)
        try:
            # If no candidate network provided, check if there is a candidate
            # network for the entire dataset that can be used instead
            if candidate_network is None:
                dataset_candidate_network = datasets.get_dataset_candidate_network(
                    dataset_id
                )
                if dataset_candidate_network is not None:
                    with open(
                        os.path.join(dataset_dir, dataset_candidate_network)
                    ) as candidate_network_file:
                        candidate_network = candidate_network_file.read()

            # Create the scenario directory
            scenario_dir = simccs_helper.create_scenario_dir(
                datasets_basepath,
                dataset_dir,
                sources=sources,
                sinks=sinks,
                candidate_network=candidate_network,
            )
            simccs_helper.write_mps_file(
                scenario_dir,
                capital_recovery_rate=capital_recovery_rate,
                num_years=num_years,
                capacity_target=capacity_target,
            )
            with open(
                simccs_helper.get_sources_file(scenario_dir)
            ) as sources_file, open(
                simccs_helper.get_sinks_file(scenario_dir)
            ) as sinks_file, open(
                simccs_helper.get_mps_file(scenario_dir)
            ) as mps_file:
                # open(
                #     simccs_helper.get_candidate_network_file(
                #         datasets_basepath, dataset_dirname, "scenario1"
                #     )
                # ) as candidate_network_file,
                sources_dp = user_storage.save_input_file(request, sources_file)
                sinks_dp = user_storage.save_input_file(request, sinks_file)
                # candidate_network_dp = user_storage.save_input_file(
                #     request, candidate_network_file
                # )
                mps_dp = user_storage.save_input_file(request, mps_file)
            return JsonResponse(
                {
                    "sources": sources_dp.productUri,
                    "sinks": sinks_dp.productUri,
                    "mps": mps_dp.productUri,
                    # "candidate-network": candidate_network_dp.productUri,
                }
            )
        except Exception as e:
            return JsonResponse({"detail": str(e)}, status=500)


@login_required
@max_concurrent_java_calls
def experiment_result(request, experiment_id):
    """
    Return a JSON object with nested GeoJSON objects.
    {
        "Network": GeoJSON,
        "Sinks":   GeoJSON,
        "Sources": GeoJSON
    }
    """
    try:
        experiment = _get_experiment(request, experiment_id)
        results_dir = _get_results_dir(experiment)
        # figure out the scenario directory
        shapefiles_dir = os.path.join(results_dir, "shapeFiles")
        geojson_dir = os.path.join(results_dir, "geojson")
        if not os.path.exists(shapefiles_dir):
            _create_shapefiles_for_result(request, experiment, results_dir)
        if not os.path.exists(geojson_dir):
            _create_geojson_for_result(results_dir)
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
        logger.exception("Failed to generate geojson result files")
        return JsonResponse({"detail": str(e)}, status=500)


@login_required
@max_concurrent_java_calls
def solution_summary(request, experiment_id):
    try:
        experiment = _get_experiment(request, experiment_id)
        results_dir = _get_results_dir(experiment)
        solution_summary = _get_solution_summary(request, experiment, results_dir)
        return JsonResponse(solution_summary)
    except Exception as e:
        logger.exception("Failed to generate solution summary")
        return JsonResponse({"detail": str(e)}, status=500)


def _get_solution_summary(request, experiment, results_dir):
    cached_solution_summary_path = os.path.join(results_dir, "solution_summary.json")
    cached_solution_summary = None
    if os.path.exists(cached_solution_summary_path):
        try:
            with open(cached_solution_summary_path) as f:
                cached_solution_summary = json.load(f)
        except Exception:
            logger.exception(f"Failed to load {cached_solution_summary_path}")
    SOLUTION_SUMMARY_CURRENT_VERSION = 1
    if (
        cached_solution_summary
        and cached_solution_summary["version"] == SOLUTION_SUMMARY_CURRENT_VERSION
    ):
        return cached_solution_summary
    else:
        solution = _load_solution(request, experiment, results_dir)
        solution_summary = {
            "version": SOLUTION_SUMMARY_CURRENT_VERSION,
            "numOpenedSources": solution.numOpenedSources,
            "numOpenedSinks": solution.numOpenedSinks,
            "targetCaptureAmount": solution.captureAmount,
            "numEdgesOpened": solution.numEdgesOpened,
            "projectLength": solution.projectLength,
            "totalCaptureCost": solution.totalAnnualCaptureCost,
            "unitCaptureCost": solution.unitCaptureCost,
            "totalTransportCost": solution.totalAnnualTransportCost,
            "unitTransportCost": solution.unitTransportCost,
            "totalStorageCost": solution.totalAnnualStorageCost,
            "unitStorageCost": solution.unitStorageCost,
            "totalCost": solution.totalCost,
            "unitTotalCost": solution.unitTotalCost,
            "crf": solution.getCRF(),
        }
        # Save solution summary to cache
        try:
            with open(cached_solution_summary_path, "w") as f:
                json.dump(solution_summary, f)
        except Exception:
            logger.exception(f"Failed to write {cached_solution_summary_path}")
        return solution_summary


def _get_experiment(request, experiment_id):
    return request.airavata_client.getExperiment(request.authz_token, experiment_id)


def _get_results_dir(experiment):
    # Get the experimentDataDir (which is the Results/ directory in v1 layout)
    return experiment.userConfigurationData.experimentDataDir


def _create_shapefiles_for_result(request, experiment, results_dir):
    # v2 experiment files layout
    if os.path.basename(os.path.dirname(os.path.dirname(results_dir))) != "Scenarios":
        sources = _get_experiment_file(request, experiment, "Sources", input_file=True)
        sinks = _get_experiment_file(request, experiment, "Sinks", input_file=True)
        dataset_id = _get_experiment_value(experiment, "Dataset-id")
        with tempfile.TemporaryDirectory() as datasets_basepath:
            dataset_dir = datasets.get_dataset_dir(dataset_id)
            # Create the scenario directory
            # TODO: add the candidatenetwork file too
            scenario_dir = simccs_helper.create_scenario_dir(
                datasets_basepath,
                dataset_dir,
                sources=sources,
                sinks=sinks,
                # Technically we don't even need these, they are loaded by
                # make_shapefiles
                # mps=mps,
                # solution=solution,
            )
            simccs_helper.make_shapefiles(scenario_dir, results_dir)
    # v1 experiment files layout
    else:
        datasets_basepath = _get_datasets_dir_from_results_dir(results_dir)
        scenario_dir = os.path.dirname(results_dir)
        simccs_helper.make_shapefiles(scenario_dir, results_dir)


# TODO: this would be a good candidate to add to SDK
def _get_experiment_file(request, experiment, name, input_file=False):
    data_product_uri = None
    if input_file:
        for exp_input in experiment.experimentInputs:
            if exp_input.name == name:
                data_product_uri = exp_input.value
    else:
        for exp_output in experiment.experimentOutputs:
            if exp_output.name == name:
                data_product_uri = exp_output.value
    if data_product_uri:
        data_product = request.airavata_client.getDataProduct(
            request.authz_token, data_product_uri)
        return user_storage.open_file(request, data_product)
    else:
        return None


# TODO: this would be a good candidate to add to SDK
def _get_experiment_value(experiment, name):
    # TODO: check type and convert to numeric types
    for exp_input in experiment.experimentInputs:
        if exp_input.name == name:
            return exp_input.value
    return None  # if not found


def _load_solution(request, experiment, results_dir):
    # v2 experiment files layout
    if os.path.basename(os.path.dirname(os.path.dirname(results_dir))) != "Scenarios":
        sources = _get_experiment_file(request, experiment, "Sources", input_file=True)
        sinks = _get_experiment_file(request, experiment, "Sinks", input_file=True)
        dataset_id = _get_experiment_value(experiment, "Dataset-id")
        with tempfile.TemporaryDirectory() as datasets_basepath:
            dataset_dir = datasets.get_dataset_dir(dataset_id)
            # Create the scenario directory
            # TODO: add the candidatenetwork file too
            scenario_dir = simccs_helper.create_scenario_dir(
                datasets_basepath,
                dataset_dir,
                sources=sources,
                sinks=sinks,
                # Technically we don't even need these, they are loaded by
                # make_shapefiles
                # mps=mps,
                # solution=solution,
            )
            return simccs_helper.load_solution(scenario_dir, results_dir)
    # v1 experiment files layout
    else:
        datasets_basepath = _get_datasets_dir_from_results_dir(results_dir)
        scenario_dir = os.path.dirname(results_dir)
        return simccs_helper.load_solution(scenario_dir, results_dir)


def _create_geojson_for_result(results_dir):
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
    dataset_dir = _get_dataset_dir_from_results_dir(results_dir)
    return os.path.basename(dataset_dir)


def _get_datasets_dir_from_results_dir(results_dir):
    dataset_dir = _get_dataset_dir_from_results_dir(results_dir)
    return os.path.dirname(dataset_dir)


def _get_dataset_dir_from_results_dir(results_dir):
    # Results dir is structured like so:
    # GATEWAY_STORAGE/{username}/Datasets/{dataset}/Scenarios/{scenario}/Results
    scenario_dir = os.path.dirname(results_dir)
    return os.path.dirname(os.path.dirname(scenario_dir))


@max_concurrent_java_calls
def candidate_network(request):

    sources = request.POST["sources"]
    sinks = request.POST["sinks"]
    dataset = request.POST["dataset"]

    with tempfile.TemporaryDirectory() as datasets_basepath:
        dataset_dir = datasets.get_dataset_dir(dataset)
        try:
            # Create the scenario directory
            scenario_dir = simccs_helper.create_scenario_dir(
                datasets_basepath, dataset_dir, sources=sources, sinks=sinks
            )
            simccs_helper.make_candidate_network_shapefiles(scenario_dir)
            candidate_network_path = simccs_helper.get_candidate_network_file(
                scenario_dir
            )
            # the shapefiles will be in the CandidateNetwork directory
            results_dir = os.path.dirname(candidate_network_path)
            _create_geojson_for_result(results_dir)
            with open(
                os.path.join(results_dir, "geojson", "Network.geojson")
            ) as network_geojson, open(
                os.path.join(results_dir, "geojson", "Sources.geojson")
            ) as sources_geojson, open(
                os.path.join(results_dir, "geojson", "Sinks.geojson")
            ) as sinks_geojson, open(
                candidate_network_path
            ) as candidate_network:
                return JsonResponse(
                    {
                        "Network": json.load(network_geojson),
                        "Sources": json.load(sources_geojson),
                        "Sinks": json.load(sinks_geojson),
                        "CandidateNetwork": candidate_network.read(),
                    }
                )
        except Exception as e:
            return JsonResponse({"detail": str(e)}, status=500)


def _get_basedata_dir(dataset_dirname):

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
        "Unable to find basedata directory for dataset {}".format(dataset_dirname)
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


@login_required
def get_case(request, case_id):
    # In this initial implementation the case data is hard coded but it is
    # really loaded from data stored in the user's storage
    case_data_dir = os.path.join(BASEDIR, "CaseData", "SimCCS_Macon")
    with open(os.path.join(case_data_dir, "samplecase.json")) as samplecase, open(
        os.path.join(case_data_dir, "Macon_Sources_SimCCS_OldFormat.geojson")
    ) as sources, open(
        os.path.join(case_data_dir, "Macon_Arkosic_Sinks_SimCCS_OldFormat.geojson")
    ) as sinks:

        # Create directory in user storage to hold the geojson files
        user_storage_dir = os.path.join("CaseData", "SimCCS_Macon")
        if not user_storage.dir_exists(request, user_storage_dir):
            user_storage.create_user_dir(request, user_storage_dir)
        sources_geosjon_path = os.path.join(
            user_storage_dir, "Macon_Sources_SimCCS_OldFormat.geojson"
        )
        if not user_storage.user_file_exists(request, sources_geosjon_path):
            sources_dp = user_storage.save(
                request, user_storage_dir, sources, content_type="application/json"
            )
            sources_dp_uri = sources_dp.productUri
        else:
            sources_dp_uri = user_storage.get_file(request, sources_geosjon_path)[
                "data-product-uri"
            ]
        sinks_geojson_path = os.path.join(
            user_storage_dir, "Macon_Arkosic_Sinks_SimCCS_OldFormat.geojson"
        )
        if not user_storage.user_file_exists(request, sinks_geojson_path):
            sinks_dp = user_storage.save(
                request, user_storage_dir, sinks, content_type="application/json"
            )
            sinks_dp_uri = sinks_dp.productUri
        else:
            sinks_dp_uri = user_storage.get_file(request, sinks_geojson_path)[
                "data-product-uri"
            ]
        samplecase_data = json.load(samplecase)
        samplecase_data["datasets"][0]["url"] = (
            reverse("django_airavata_api:download_file")
            + "?"
            + urlencode({"data-product-uri": sources_dp_uri})
        )
        samplecase_data["datasets"][1]["url"] = (
            reverse("django_airavata_api:download_file")
            + "?"
            + urlencode({"data-product-uri": sinks_dp_uri})
        )
        return JsonResponse(samplecase_data)


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Only the owner has write access
        return request.user == obj.owner


class IsProjectOwner(permissions.BasePermission):
    "Check if user is owner of the project to which this object belongs"

    def has_object_permission(self, request, view, obj):
        return request.user == obj.simccs_project.owner


class SimccsProjectViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SimccsProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        request = self.request
        return models.SimccsProject.filter_by_user(request)

    @action(detail=True, methods=['post'])
    def transfer_ownership(self, request, pk=None):
        simccs_project = self.get_object()
        serializer = self.get_serializer(simccs_project, data=request.data)
        serializer.is_valid(raise_exception=True)
        new_owner = serializer.validated_data['new_owner']
        new_owner_user = get_user_model().objects.get(username=new_owner)
        # update owner field
        serializer.instance.owner = new_owner_user
        serializer.instance.save()
        return Response(serializer.data)


class CaseViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CaseSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # only return Cases that the user is the project's owner or the user is
        # a member of the project's group
        request = self.request
        group_ids = models.get_user_group_membership_ids(request)
        queryset = models.Case.objects.filter(
            Q(simccs_project__owner=request.user) |
            Q(simccs_project__group__in=group_ids))
        simccs_project = self.request.query_params.get('project', None)
        if simccs_project is not None:
            queryset = queryset.filter(simccs_project=simccs_project)
        return queryset

    @action(detail=True,
            methods=['post'],
            permission_classes=[permissions.IsAuthenticated, IsProjectOwner])
    def claim_ownership(self, request, pk=None):
        "Only Project owner can claim ownership of cases"
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # update owner field
        serializer.instance.owner = request.user
        serializer.instance.save()
        return Response(serializer.data)


class DatasetViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.DatasetSerializer
    parser_classes = [parsers.MultiPartParser]
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # only return Datasets that the user is the project's owner or that
        # user is a member of the project's group
        request = self.request
        group_ids = models.get_user_group_membership_ids(request)
        queryset = models.Dataset.objects.filter(
            Q(simccs_project__owner=request.user) |
            Q(simccs_project__group__in=group_ids))
        simccs_project = self.request.query_params.get('project', None)
        if simccs_project is not None:
            queryset = queryset.filter(simccs_project=simccs_project)
        return queryset

    @action(detail=True,
            methods=['post'],
            permission_classes=[permissions.IsAuthenticated, IsProjectOwner])
    def claim_ownership(self, request, pk=None):
        "Only Project owner can claim ownership of datasets"
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # update owner field
        serializer.instance.owner = request.user
        serializer.instance.save()
        return Response(serializer.data)


class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # only return Workspaces that the user is the case's project's owner or
        # the user is a member of the case's project's group
        request = self.request
        group_ids = models.get_user_group_membership_ids(request)
        queryset = models.Workspace.objects.filter(
            Q(case__simccs_project__owner=request.user) |
            Q(case__simccs_project__group__in=group_ids))
        simccs_project = self.request.query_params.get('project', None)
        if simccs_project is not None:
            queryset = queryset.filter(case__simccs_project=simccs_project)
        return queryset
