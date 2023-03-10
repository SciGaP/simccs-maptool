# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import glob
import io
import json
import logging
import os
import tempfile
from contextlib import ContextDecorator, contextmanager
from threading import BoundedSemaphore

import shapefile
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic import TemplateView
from rest_framework import parsers, permissions, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from simccs_maptool import datasets, models, serializers

from . import simccs_helper

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


@api_view(['POST'])
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
    mps_filename = request.POST.get("mpsFilename", None)

    with tempfile.TemporaryDirectory() as datasets_basepath:
        dataset_dir = datasets.get_dataset_dir(dataset_id)
        try:
            # If no candidate network provided, check if there is a candidate
            # network for the entire dataset that can be used instead
            # if candidate_network is None:
            #     dataset_candidate_network = datasets.get_dataset_candidate_network(
            #         dataset_id
            #     )
            #     if dataset_candidate_network is not None:
            #         with open(
            #             os.path.join(dataset_dir, dataset_candidate_network)
            #         ) as candidate_network_file:
            #             candidate_network = candidate_network_file.read()

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
                filename=mps_filename,
            )
            with open(
                simccs_helper.get_sources_file(scenario_dir)
            ) as sources_file, open(
                simccs_helper.get_sinks_file(scenario_dir)
            ) as sinks_file, open(
                simccs_helper.get_mps_file(scenario_dir)
            ) as mps_file, open(
                simccs_helper.get_candidate_network_file(scenario_dir)
            ) as candidate_network_file:
                sources_dp = user_storage.save_input_file(request, sources_file)
                sinks_dp = user_storage.save_input_file(request, sinks_file)
                candidate_network_dp = user_storage.save_input_file(
                    request, candidate_network_file
                )
                mps_dp = user_storage.save_input_file(request, mps_file)
            return JsonResponse(
                {
                    "sources": sources_dp.productUri,
                    "sinks": sinks_dp.productUri,
                    "mps": mps_dp.productUri,
                    "candidate-network": candidate_network_dp.productUri,
                }
            )
        except Exception as e:
            logger.exception("Failed to generate mps file")
            return JsonResponse({"detail": str(e)}, status=500)

@api_view(['GET'])
@max_concurrent_java_calls
def experiment_result(request, experiment_id):
    """
    Return a JSON object with nested GeoJSON objects.
    {
        "Network": GeoJSON,
        "Sinks":   GeoJSON,
        "Sources": GeoJSON,
        "CandidateNetwork": GeoJSON,
        "CandidateSinks": GeoJSON,
        "CandidateSources": GeoJSON
    }
    """
    try:
        # Load experiment to check if user has access to this experiment
        experiment = _get_experiment(request, experiment_id)
        if (
            not user_storage.user_file_exists(request,
                                              os.path.join("geojson", "Network.geojson"),
                                              experiment_id=experiment_id)
            or not user_storage.user_file_exists(request,
                                                 os.path.join("geojson", "Sources.geojson"),
                                                 experiment_id=experiment_id)
            or not user_storage.user_file_exists(request,
                                                 os.path.join("geojson", "Sinks.geojson"),
                                                 experiment_id=experiment_id)
            or not user_storage.user_file_exists(request,
                                                 os.path.join("geojson",
                                                              "CandidateNetwork.geojson"),
                                                 experiment_id=experiment_id)
            or not user_storage.user_file_exists(request,
                                                 os.path.join("geojson",
                                                              "CandidateSources.geojson"),
                                                 experiment_id=experiment_id)
            or not user_storage.user_file_exists(request,
                                                 os.path.join("geojson",
                                                              "CandidateSinks.geojson"),
                                                 experiment_id=experiment_id)
        ):
            # Generate shape files and geojson files
            with experiment_scenario_dir(request, experiment) as scenario_dir:

                results_dir = simccs_helper.get_results_dir(scenario_dir)
                simccs_helper.make_shapefiles(scenario_dir)
                simccs_helper.make_candidate_network_shapefiles(scenario_dir)
                _create_geojson_for_result(results_dir)
                _create_geojson_for_candidate_network(scenario_dir)

                # if experiment owner, save the shapeFiles and geojson files in
                # the experiment directory
                if request.user.username == experiment.userName:
                    _copy_directory_to_experiment(
                        request, experiment, simccs_helper.get_shapefiles_dir(scenario_dir))
                    _copy_directory_to_experiment(
                        request,
                        experiment,
                        simccs_helper.get_candidate_network_shapefiles_dir(scenario_dir),
                        lambda filename: "Candidate" + filename)
                    _copy_directory_to_experiment(
                        request, experiment, os.path.join(results_dir, "geojson"))

                # otherwise, can't save the generated files, so just return the
                # generated geojson files to the user
                else:
                    with open(
                        os.path.join(results_dir, "geojson", "Network.geojson")
                    ) as network_geojson, open(
                        os.path.join(results_dir, "geojson", "Sources.geojson")
                    ) as sources_geojson, open(
                        os.path.join(results_dir, "geojson", "Sinks.geojson")
                    ) as sinks_geojson, open(
                        os.path.join(results_dir, "geojson", "CandidateNetwork.geojson")
                    ) as candnet_geojson, open(
                        os.path.join(results_dir, "geojson", "CandidateSources.geojson")
                    ) as candsources_geojson, open(
                        os.path.join(results_dir, "geojson", "CandidateSinks.geojson")
                    ) as candsinks_geojson:
                        return JsonResponse(
                            {
                                "Network": json.load(network_geojson),
                                "Sources": json.load(sources_geojson),
                                "Sinks": json.load(sinks_geojson),
                                "CandidateNetwork": json.load(candnet_geojson),
                                "CandidateSources": json.load(candsources_geojson),
                                "CandidateSinks": json.load(candsinks_geojson),
                            }
                        )

        with _open_experiment_filepath(
            request, experiment, os.path.join("geojson", "Network.geojson")
        ) as network_geojson, _open_experiment_filepath(
            request, experiment, os.path.join("geojson", "Sources.geojson")
        ) as sources_geojson, _open_experiment_filepath(
            request, experiment, os.path.join("geojson", "Sinks.geojson")
        ) as sinks_geojson, _open_experiment_filepath(
            request, experiment, os.path.join("geojson", "CandidateNetwork.geojson")
        ) as candnet_geojson, _open_experiment_filepath(
            request, experiment, os.path.join("geojson", "CandidateSources.geojson")
        ) as candsources_geojson, _open_experiment_filepath(
            request, experiment, os.path.join("geojson", "CandidateSinks.geojson")
        ) as candsinks_geojson:
            return JsonResponse(
                {
                    "Network": json.load(network_geojson),
                    "Sources": json.load(sources_geojson),
                    "Sinks": json.load(sinks_geojson),
                    "CandidateNetwork": json.load(candnet_geojson),
                    "CandidateSources": json.load(candsources_geojson),
                    "CandidateSinks": json.load(candsinks_geojson),
                }
            )
    except Exception as e:
        logger.exception("Failed to generate geojson result files")
        return JsonResponse({"detail": str(e)}, status=500)


@api_view(['GET'])
@max_concurrent_java_calls
def solution_summary(request, experiment_id):
    try:
        experiment = _get_experiment(request, experiment_id)
        solution_summary = _get_solution_summary(request, experiment)
        return JsonResponse(solution_summary)
    except Exception as e:
        logger.exception("Failed to generate solution summary")
        return JsonResponse({"detail": str(e)}, status=500)


def _get_solution_summary(request, experiment):
    experiment_id = experiment.experimentId
    cached_solution_summary = None
    if user_storage.user_file_exists(request,
                                     "solution_summary.json",
                                     experiment_id=experiment_id):
        try:
            with _open_experiment_filepath(request, experiment, "solution_summary.json") as f:
                cached_solution_summary = json.load(f)
        except Exception:
            logger.exception(f"Failed to load solution_summary.json for "
                             f"experiment {experiment.experimentId}")
    SOLUTION_SUMMARY_CURRENT_VERSION = 1
    if (
        cached_solution_summary
        and cached_solution_summary["version"] == SOLUTION_SUMMARY_CURRENT_VERSION
    ):
        return cached_solution_summary
    else:

        # Load solution and generate solution summary JSON
        with experiment_scenario_dir(request, experiment) as scenario_dir:
            solution = simccs_helper.load_solution(scenario_dir)
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
            if request.user.username == experiment.userName:
                try:
                    solution_file = io.BytesIO(json.dumps(solution_summary).encode())
                    user_storage.save(request,
                                      "",
                                      solution_file,
                                      name="solution_summary.json",
                                      experiment_id=experiment_id)
                except Exception:
                    logger.exception(f"Failed to write solution_summary.json "
                                     f"for experiment {experiment_id}")
            return solution_summary


def _get_experiment(request, experiment_id):
    return request.airavata_client.getExperiment(request.authz_token, experiment_id)


@contextmanager
def experiment_scenario_dir(request, experiment):
    "Generate a scenario directory from the experiment input and output files"
    sources = _get_experiment_file(request, experiment, "Sources", input_file=True)
    sinks = _get_experiment_file(request, experiment, "Sinks", input_file=True)
    mps = _get_experiment_file(request, experiment, "Cplex-input-file", input_file=True)
    candidate_network = _get_experiment_file(
        request, experiment, "Candidate-Network", input_file=True)
    solution = _get_experiment_file(request, experiment, "Cplex-solution")
    dataset_id = _get_experiment_value(experiment, "Dataset-id")
    # FIXME: users can't specify the dataset id and it has no default, so it may
    # not be set but we'll just assume that it is Lower48US
    if not dataset_id:
        dataset_id = "Lower48US"
    with tempfile.TemporaryDirectory() as datasets_basepath:
        dataset_dir = datasets.get_dataset_dir(dataset_id)
        # Create the scenario directory
        scenario_dir = simccs_helper.create_scenario_dir(
            datasets_basepath,
            dataset_dir,
            sources=sources,
            sinks=sinks,
            mps=mps,
            solution=solution,
            candidate_network=candidate_network,
        )
        yield scenario_dir


def _copy_directory_to_experiment(request,
                                  experiment,
                                  directory,
                                  filename_mapping=None):
    filename_mapping = filename_mapping if filename_mapping is not None else lambda n: n
    experiment_id = experiment.experimentId
    dir_name = os.path.basename(directory)
    if not user_storage.dir_exists(request, dir_name, experiment_id=experiment_id):
        user_storage.create_user_dir(request, dir_name, experiment_id=experiment_id)
    listings = os.listdir(directory)
    for listing in listings:
        path = os.path.join(directory, listing)
        if os.path.isfile(path):
            with open(path, "rb") as f:
                filename = filename_mapping(listing)
                user_storage.save(request,
                                  dir_name,
                                  f,
                                  name=filename,
                                  experiment_id=experiment_id)


def _open_experiment_filepath(request, experiment, path):
    data_product_uri = user_storage.user_file_exists(
        request, path, experiment_id=experiment.experimentId)
    if data_product_uri:
        return user_storage.open_file(request, data_product_uri=data_product_uri)
    raise Exception(f"{path} does not exist in experiment {experiment.experimentId}")


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
        logger.warning(
            f"Could not find experiment file {name} (input_file={input_file})")
        return None


# TODO: this would be a good candidate to add to SDK
def _get_experiment_value(experiment, name):
    # TODO: check type and convert to numeric types
    for exp_input in experiment.experimentInputs:
        if exp_input.name == name:
            return exp_input.value
    return None  # if not found


def _create_geojson_for_result(results_dir):
    network_sf = shapefile.Reader(os.path.join(results_dir, "shapeFiles", "Network"))
    sinks_sf = shapefile.Reader(os.path.join(results_dir, "shapeFiles", "Sinks"))
    sources_sf = shapefile.Reader(os.path.join(results_dir, "shapeFiles", "Sources"))
    geojson_dir = os.path.join(results_dir, "geojson")
    os.makedirs(geojson_dir, exist_ok=True)
    with open(os.path.join(geojson_dir, "Network.geojson"), "w") as network_geojson_f:
        _write_shapefile_to_geojson(network_sf, network_geojson_f)
    with open(os.path.join(geojson_dir, "Sinks.geojson"), "w") as sinks_geojson_f:
        _write_shapefile_to_geojson(sinks_sf, sinks_geojson_f)
    with open(os.path.join(geojson_dir, "Sources.geojson"), "w") as sources_geojson_f:
        _write_shapefile_to_geojson(sources_sf, sources_geojson_f)


def _create_geojson_for_candidate_network(scenario_dir):
    results_dir = simccs_helper.get_results_dir(scenario_dir)
    shapefiles_dir = simccs_helper.get_candidate_network_shapefiles_dir(scenario_dir)
    candidate_network_sf = shapefile.Reader(os.path.join(shapefiles_dir, "Network"))
    candidate_sinks_sf = shapefile.Reader(os.path.join(shapefiles_dir, "Sinks"))
    candidate_sources_sf = shapefile.Reader(os.path.join(shapefiles_dir, "Sources"))
    geojson_dir = os.path.join(results_dir, "geojson")
    os.makedirs(geojson_dir, exist_ok=True)
    with open(os.path.join(geojson_dir, "CandidateNetwork.geojson"), "w") as candnet_geojson_f:
        _write_shapefile_to_geojson(candidate_network_sf, candnet_geojson_f)
    with open(os.path.join(geojson_dir, "CandidateSinks.geojson"), "w") as candsinks_geojson_f:
        _write_shapefile_to_geojson(candidate_sinks_sf, candsinks_geojson_f)
    with open(os.path.join(geojson_dir, "CandidateSources.geojson"), "w") as candsources_geojson_f:
        _write_shapefile_to_geojson(candidate_sources_sf, candsources_geojson_f)


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


@api_view(['POST'])
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

    def get_object(self):
        project = super().get_object()
        # Keep track of most recent project that the user uses
        models.UserPreference.objects.update_or_create(
            user=self.request.user,
            name="most_recent_project",
            defaults=dict(value=project.id))
        return project

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
        queryset = self._get_base_queryset()
        if self.action != 'undelete':
            queryset = queryset.filter(deleted=False)
        return queryset

    def perform_destroy(self, instance):
        instance.deleted = True
        instance.save()

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

    @action(detail=False)
    def list_deleted(self, request):
        queryset = self._get_base_queryset()
        queryset = queryset.filter(deleted=True)
        instances = queryset.all()
        serializer = self.get_serializer(instances, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def undelete(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        serializer.instance.deleted = False
        serializer.instance.save()
        return Response(serializer.data)

    def _get_base_queryset(self):
        request = self.request
        group_ids = models.get_user_group_membership_ids(request)
        queryset = models.Dataset.objects.filter(
            Q(simccs_project__owner=request.user) |
            Q(simccs_project__group__in=group_ids))
        simccs_project = self.request.query_params.get('project', None)
        if simccs_project is not None:
            queryset = queryset.filter(simccs_project=simccs_project)
        return queryset


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
        owner = self.request.query_params.get('owner', None)
        if owner is not None:
            queryset = queryset.filter(owner__username=owner)
        return queryset


class ScenarioExperimentNoteViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ScenarioExperimentNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # only return Experiments that the user is the case's project's owner or
        # the user is a member of the case's project's group
        request = self.request
        group_ids = models.get_user_group_membership_ids(request)
        queryset = models.ScenarioExperimentNote.objects.filter(
            Q(experiment__scenario__workspace__case__simccs_project__owner=request.user) |
            Q(experiment__scenario__workspace__case__simccs_project__group__in=group_ids))
        return queryset
