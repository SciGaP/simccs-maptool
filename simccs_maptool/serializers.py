import io
import logging
import os

from django.conf import settings
import pandas as pd
import geopandas as gpd
from airavata.model.workspace.ttypes import Project
from airavata_django_portal_sdk import urls as sdk_urls, user_storage
from rest_framework import serializers, validators

from simccs_maptool import models
from airavata.model.group.ttypes import ResourcePermissionType
from airavata.model.status.ttypes import ExperimentState
from collections import defaultdict
from django.urls import reverse

logger = logging.getLogger(__name__)
BASEDIR = os.path.dirname(os.path.abspath(__file__))


class CSVField(serializers.Field):
    def to_representation(self, value):
        """Convert comma-delimited string to list of numbers."""
        if value is not None and value != "":
            return list(map(self.to_item_representation, value.split(",")))
        else:
            return []

    def to_item_representation(self, value):
        """Convert item in the list to representation."""
        return value

    def to_internal_value(self, data):
        """Convert list of numbers to comma-delimited string."""
        return ",".join(map(self.to_item_internal_value, data))

    def to_item_internal_value(self, data):
        """Convert list member to internal value."""
        return data


class BboxField(CSVField):
    def to_item_representation(self, value):
        return float(value)

    def to_item_internal_value(self, data):
        return str(data)


class UniqueToUserValidator(validators.UniqueValidator):
    requires_context = True

    def __init__(self, queryset, user_field, message=None, lookup="exact"):
        self.user_field = user_field
        super().__init__(queryset, message=message, lookup=lookup)

    def set_context(self, serializer_field):
        self.user = serializer_field.context["request"].user
        return super().set_context(serializer_field)

    def filter_queryset(self, value, queryset):
        # filter by current user
        queryset = queryset.filter(**{self.user_field: self.user})
        return super().filter_queryset(value, queryset)


class SimccsProjectSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field='username', read_only=True)
    airavata_project = serializers.CharField(read_only=True)
    new_owner = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Username of new project owner, used with transfer_ownership")
    userHasWriteAccess = serializers.SerializerMethodField()

    class Meta:
        model = models.SimccsProject
        fields = ("id",
                  "name",
                  "owner",
                  "group",
                  "airavata_project",
                  "new_owner",
                  "userHasWriteAccess")

    def create(self, validated_data):
        request = self.context["request"]
        simccs_project = models.SimccsProject.objects.create(
            owner=request.user, **validated_data)
        airavata_project_id = self._create_airavata_project(validated_data)
        simccs_project.airavata_project = airavata_project_id
        simccs_project.save()
        if validated_data["group"]:
            # share project with group
            request.airavata_client.shareResourceWithGroups(
                request.authz_token, airavata_project_id,
                {validated_data["group"]: ResourcePermissionType.READ})
        return simccs_project

    def update(self, instance, validated_data):
        request = self.context["request"]
        instance.name = validated_data["name"]
        # Normally the airavata_project is created in create(), but for
        # cases/datasets that were created prior to the SimccsProject data
        # model, those were assigned a default SimccsProject that the data
        # migration was unable to create an airavata_project for
        if instance.airavata_project is None:
            instance.airavata_project = self._create_airavata_project(validated_data)
        old_group = instance.group
        instance.group = validated_data["group"]
        if old_group != instance.group:
            # if the group changes, update the sharing of the Airavata Project
            if old_group:
                request.airavata_client.revokeSharingOfResourceFromGroups(
                    request.authz_token, instance.airavata_project,
                    {old_group: ResourcePermissionType.READ})
            if validated_data["group"]:
                request.airavata_client.shareResourceWithGroups(
                    request.authz_token, instance.airavata_project,
                    {validated_data["group"]: ResourcePermissionType.READ})
        instance.save()
        return instance

    def validate_new_owner(self, value):
        # validate_new_owner is only called if new_owner was included in request
        # validate that the current action is transfer_ownership
        request = self.context['request']
        view = self.context['view']
        action = view.action
        if action != 'transfer_ownership':
            raise serializers.ValidationError(
                "new_owner is only allows in transfer_ownership action")
        # validate that there is a group
        if self.instance.group is None:
            raise serializers.ValidationError(
                "cannot assign new_owner until group has been assigned")
        # validate that new_owner is a member of the group
        group = request.profile_service['group_manager'].getGroup(
            request.authz_token, self.instance.group)
        user_id = value + "@" + settings.GATEWAY_ID
        if user_id not in group.members:
            raise serializers.ValidationError(
                f"{value} is not a member of group {group.name}")

        return value

    def get_userHasWriteAccess(self, instance):
        return self.context['request'].user == instance.owner

    def _create_airavata_project(self, validated_data):
        request = self.context['request']
        # create an airavata project for this SimCCS project and store its ID
        airavata_project = Project(
            owner=request.user.username,
            gatewayId=settings.GATEWAY_ID,
            name="simccs:" + validated_data["name"])
        airavata_project_id = request.airavata_client.createProject(
            request.authz_token, settings.GATEWAY_ID, airavata_project)
        return airavata_project_id


class SimccsProjectPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context['request']
        return models.SimccsProject.filter_by_user(request)


class DatasetSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        write_only=True,
        required=False,
        help_text="Required when creating a new Dataset",
    )
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(
        required=True,
        validators=[UniqueToUserValidator(models.Dataset.objects.all(), "owner")],
    )
    owner = serializers.SlugRelatedField(slug_field='username', read_only=True)
    data_product_uri = serializers.CharField(read_only=True)
    original_data_product_uri = serializers.CharField(read_only=True)
    description = serializers.CharField(
        style={"base_template": "textarea.html"}, allow_blank=True
    )
    original_filename = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    simccs_project = SimccsProjectPrimaryKeyRelatedField()
    userIsProjectOwner = serializers.SerializerMethodField()

    class Meta:
        model = models.Dataset
        fields = "__all__"

    def create(self, validated_data):
        file = validated_data.pop("file")
        request = self.context["request"]
        original_data_product = user_storage.save(
            request, "Datasets", file, name=file.name, content_type=file.content_type
        )
        dataset = models.Dataset.objects.create(
            **validated_data,
            owner=request.user,
            original_data_product_uri=original_data_product.productUri,
        )
        transformed_file = self._transform_file(
            user_storage.open_file(request, original_data_product),
            dataset_type=validated_data["type"],
            content_type=file.content_type
        )
        if transformed_file:
            data_product = user_storage.save(
                request,
                "Datasets",
                transformed_file,
                name=transformed_file.name,
                content_type="application/geo+json",
            )
            dataset.data_product_uri = data_product.productUri
            dataset.save()
        return dataset

    def update(self, instance, validated_data):
        # TODO: update file?
        instance.name = validated_data["name"]
        instance.description = validated_data["description"]
        instance.save()
        return instance

    def _transform_file(self, input_file, dataset_type, content_type):
        # transform the file and return the transformed file (GeoJSON)
        if content_type.startswith("text/"):
            return self._transform_text_file(input_file)
        else:
            raise Exception(f"Unrecognized file type {content_type}")

    def _transform_text_file(self, input_file):
        # assume the delimiter is "tab"
        rawdata = pd.read_csv(input_file, sep="\t")
        # convert to a geopandas object
        geodata = gpd.GeoDataFrame(
            rawdata, geometry=gpd.points_from_xy(rawdata.LON, rawdata.LAT)
        )
        # set the projection
        geodata.set_crs(epsg=4326)
        outputfile = input_file.name.split(".")[0] + ".geojson"
        # Write out GeoJSON to in-memory file object
        f = io.BytesIO()
        geodata.to_file(f, driver="GeoJSON")
        f.seek(0)
        f.name = outputfile
        return f

    def get_original_filename(self, dataset):
        request = self.context["request"]
        try:
            data_product = request.airavata_client.getDataProduct(
                request.authz_token, dataset.original_data_product_uri
            )
            return data_product.productName
        except Exception:
            return "N/A"

    def get_url(self, dataset):
        return sdk_urls.get_download_url(dataset.data_product_uri)

    def get_userIsProjectOwner(self, instance):
        return self.context['request'].user == instance.simccs_project.owner


class MaptoolDataSerializer(serializers.ModelSerializer):
    bbox = BboxField(required=False, allow_null=True)
    popup = CSVField(required=False, allow_null=True)

    class Meta:
        model = models.MaptoolData
        fields = ["bbox", "style", "dataset", "popup"]


class MaptoolConfigSerializer(serializers.ModelSerializer):
    data = MaptoolDataSerializer(many=True, allow_null=True)
    bbox = BboxField(required=False, allow_null=True)

    class Meta:
        model = models.MaptoolConfig
        fields = ["bbox", "data"]


class CaseSerializer(serializers.ModelSerializer):
    maptool = MaptoolConfigSerializer(required=True, allow_null=True)
    owner = serializers.SlugRelatedField(slug_field='username', read_only=True)
    title = serializers.CharField(
        required=True,
        validators=[UniqueToUserValidator(models.Case.objects.all(), "owner")],
    )
    description = serializers.CharField(
        style={"base_template": "textarea.html"}, allow_blank=True
    )
    datasets = serializers.SerializerMethodField()
    userHasWriteAccess = serializers.SerializerMethodField()
    simccs_project = SimccsProjectPrimaryKeyRelatedField()
    userIsProjectOwner = serializers.SerializerMethodField()

    class Meta:
        model = models.Case
        fields = "__all__"

    def create(self, validated_data):
        request = self.context["request"]
        maptool = validated_data.pop("maptool")
        data = maptool.pop("data")
        case = models.Case.objects.create(owner=request.user, **validated_data)
        maptool_inst = models.MaptoolConfig.objects.create(case=case, **maptool)
        for datum in data:
            models.MaptoolData.objects.create(maptool_config=maptool_inst, **datum)
        return case

    def update(self, instance, validated_data):
        # update MaptoolConfig
        maptool = validated_data.pop("maptool")
        instance.maptool.bbox = maptool["bbox"]
        instance.maptool.save()
        # add/update MaptoolConfig.data entries
        data = maptool.pop("data")
        dataset_ids = []
        for datum in data:
            dataset = datum.pop("dataset")
            dataset_ids.append(dataset.id)
            models.MaptoolData.objects.update_or_create(
                maptool_config=instance.maptool, dataset=dataset, defaults=datum
            )
        # Remove datasets that have been removed from case
        instance.maptool.data.exclude(dataset_id__in=dataset_ids).delete()
        # update Case - description, title
        instance.description = validated_data["description"]
        instance.title = validated_data["title"]
        instance.save()
        return instance

    def get_datasets(self, instance):
        datasets = map(lambda d: d.dataset, instance.maptool.data.all())
        serializer = DatasetSerializer(
            datasets, many=True, context={"request": self.context["request"]}
        )
        return serializer.data

    def get_userHasWriteAccess(self, instance):
        return self.context['request'].user == instance.owner

    def get_userIsProjectOwner(self, instance):
        return self.context['request'].user == instance.simccs_project.owner


class ParametersSerializer(serializers.Serializer):
    """Convert between a list of k/v dicts (internal) and a dict (external)"""
    name = serializers.CharField(max_length=255)
    value = serializers.CharField(max_length=255)

    def to_internal_value(self, data):
        parameters = []
        for k, v in data.items():
            parameters.append(dict(name=k, value=v))
        return parameters

    def to_representation(self, instance):
        result = {}
        for parameter in instance.all():
            result[parameter.name] = parameter.value
        return result


class ScenarioSourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ScenarioSource
        fields = ('source_id', 'dataset')


class ScenarioSinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ScenarioSink
        fields = ('sink_id', 'dataset')


class ScenarioExperimentSerializer(serializers.ModelSerializer):
    experiment_id = serializers.CharField(max_length=255)
    parameters = ParametersSerializer()

    class Meta:
        model = models.ScenarioExperiment
        fields = ('experiment_id', 'parameters')

    def to_representation(self, instance):
        request = self.context['request']
        experiment = request.airavata_client.getExperiment(
            request.authz_token, instance.experiment_id)
        result = super().to_representation(instance)
        result['experiment_name'] = experiment.experimentName
        result['experiment_url'] = reverse(
            "django_airavata_workspace:view_experiment", args=[instance.experiment_id])
        result['experiment_state'] = ExperimentState._VALUES_TO_NAMES[
            experiment.experimentStatus[-1].state]
        result['experiment_result'] = reverse(
            "simccs_maptool:experiment-result", args=[instance.experiment_id])
        result['solution_summary'] = reverse(
            "simccs_maptool:solution-summary", args=[instance.experiment_id])
        return result


class ScenarioSerializer(serializers.ModelSerializer):
    # Need the id to not be readonly so it is available for updates
    id = serializers.IntegerField(label='ID', required=False)
    parameters = ParametersSerializer()
    sources = ScenarioSourceSerializer(many=True)
    sinks = ScenarioSinkSerializer(many=True)
    experiments = ScenarioExperimentSerializer(many=True)

    class Meta:
        model = models.Scenario
        fields = ("id", "title", "sources", "sinks", "experiments", "parameters")


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field='username', read_only=True)
    description = serializers.CharField(
        style={"base_template": "textarea.html"}, allow_blank=True
    )
    scenarios = ScenarioSerializer(many=True)

    class Meta:
        model = models.Workspace
        fields = ("id", "name", "description", "owner", "scenarios", "case")

    def create(self, validated_data):
        request = self.context["request"]
        scenarios = validated_data.pop("scenarios")
        workspace = models.Workspace.objects.create(
            owner=request.user, **validated_data)
        for scenario in scenarios:
            sources = scenario.pop("sources")
            sinks = scenario.pop("sinks")
            experiments = scenario.pop("experiments")
            parameters = scenario.pop("parameters")
            scenario_inst = models.Scenario.objects.create(
                workspace=workspace, **scenario)
            for parameter in parameters:
                models.ScenarioParameter.objects.create(
                    scenario=scenario_inst, **parameter)
            for source in sources:
                models.ScenarioSource.objects.create(scenario=scenario_inst, **source)
            for sink in sinks:
                models.ScenarioSink.objects.create(scenario=scenario_inst, **sink)
            for experiment in experiments:
                experiment_parameters = experiment.pop("parameters")
                experiment_inst = models.ScenarioExperiment.objects.create(
                    scenario=scenario_inst, **experiment)
                for parameter in experiment_parameters:
                    models.ScenarioExperimentParameter.objects.create(
                        experiment=experiment_inst, **parameter
                    )
        return workspace

    def update(self, instance, validated_data):
        logger.debug(f"workspace update {validated_data}")
        scenarios = validated_data.pop("scenarios")
        for scenario in scenarios:
            sources = scenario.pop("sources")
            sinks = scenario.pop("sinks")
            experiments = scenario.pop("experiments")
            parameters = scenario.pop("parameters")
            logger.debug(f"scenario={scenario}")
            scenario_inst = models.Scenario(workspace=instance, **scenario)
            scenario_inst.save()
            parameter_names = []
            for parameter in parameters:
                name = parameter.pop("name")
                parameter_names.append(name)
                models.ScenarioParameter.objects.update_or_create(
                    scenario=scenario_inst, name=name, defaults=parameter)
            # Delete any parameters no longer listed
            scenario_inst.parameters.exclude(name__in=parameter_names).delete()
            source_ids = defaultdict(list)
            for source in sources:
                source_id = source.pop("source_id")
                dataset = source.pop("dataset")
                source_ids[dataset].append(source_id)
                models.ScenarioSource.objects.update_or_create(
                    scenario=scenario_inst, source_id=source_id, dataset=dataset
                )
            # Delete any sources no longer listed
            for dataset, source_id_list in source_ids.items():
                scenario_inst.sources.filter(dataset=dataset).exclude(
                    source_id__in=source_id_list).delete()
            sink_ids = defaultdict(list)
            for sink in sinks:
                sink_id = sink.pop("sink_id")
                dataset = sink.pop("dataset")
                sink_ids[dataset].append(sink_id)
                models.ScenarioSink.objects.update_or_create(
                    scenario=scenario_inst, sink_id=sink_id, dataset=dataset
                )
            # Delete any sinks no longer listed
            for dataset, sink_id_list in sink_ids.items():
                scenario_inst.sinks.filter(dataset=dataset).exclude(
                    sink_id__in=sink_id_list).delete()
            experiment_ids = []
            for experiment in experiments:
                experiment_id = experiment.pop("experiment_id")
                experiment_ids.append(experiment_id)
                experiment_parameters = experiment.pop("parameters")
                experiment_inst, created = models.ScenarioExperiment.objects.update_or_create(
                    scenario=scenario_inst, experiment_id=experiment_id)
                parameter_names = []
                for parameter in experiment_parameters:
                    name = parameter.pop("name")
                    parameter_names.append(name)
                    models.ScenarioExperimentParameter.objects.update_or_create(
                        experiment=experiment_inst, name=name, defaults=parameter)
                # Delete any parameters no longer listed
                experiment_inst.parameters.exclude(name__in=parameter_names).delete()
            # Delete any experiments no longer listed
            scenario_inst.experiments.exclude(experiment_id__in=experiment_ids).delete()
        # update workspace name and description
        instance.name = validated_data['name']
        instance.description = validated_data['description']
        instance.save()
        return instance
