import io
import logging
import os

from django.db import transaction
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
from functools import partial

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

    def __call__(self, value, serializer_field):
        self.user = serializer_field.context["request"].user
        return super().__call__(value, serializer_field)

    def filter_queryset(self, value, queryset, field_name):
        # filter by current user
        queryset = queryset.filter(**{self.user_field: self.user})
        return super().filter_queryset(value, queryset, field_name)


class SimccsProjectSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field='username', read_only=True)
    airavata_project = serializers.CharField(read_only=True)
    new_owner = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Username of new project owner, used with transfer_ownership")
    userHasWriteAccess = serializers.SerializerMethodField()
    userMostRecentProject = serializers.SerializerMethodField()
    name = serializers.CharField(
        required=True,
        validators=[UniqueToUserValidator(models.SimccsProject.objects.all(), "owner")],
    )

    class Meta:
        model = models.SimccsProject
        fields = ("id",
                  "name",
                  "owner",
                  "group",
                  "airavata_project",
                  "new_owner",
                  "userHasWriteAccess",
                  "userMostRecentProject")

    def create(self, validated_data):
        request = self.context["request"]
        simccs_project = models.SimccsProject.objects.create(
            owner=request.user, **validated_data)
        airavata_project_id = self._create_airavata_project(validated_data)
        simccs_project.airavata_project = airavata_project_id
        simccs_project.save()
        if validated_data.get("group", None) is not None:
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

    def get_userMostRecentProject(self, instance):
        request = self.context['request']
        return models.UserPreference.objects.filter(
            name="most_recent_project", user=request.user, value=instance.id).exists()


class SimccsProjectPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context['request']
        return models.SimccsProject.filter_by_user(request)


class DatasetVersionSerializer(serializers.ModelSerializer):

    url = serializers.SerializerMethodField()
    original_url = serializers.SerializerMethodField()
    original_filename = serializers.SerializerMethodField()
    dataset = serializers.HyperlinkedRelatedField(view_name='simccs_maptool:dataset-detail',
                                                  read_only=True)

    class Meta:
        model = models.DatasetVersion
        fields = ['version',
                  'data_product_uri',
                  'original_data_product_uri',
                  'created',
                  'url',
                  'original_url',
                  'original_filename',
                  'dataset',
                  ]

    def get_url(self, dataset_version):
        if dataset_version.data_product_uri:
            return sdk_urls.get_download_url(dataset_version.data_product_uri)
        else:
            return None

    def get_original_url(self, dataset_version):
        return sdk_urls.get_download_url(dataset_version.original_data_product_uri)

    def get_original_filename(self, dataset):
        request = self.context["request"]
        try:
            data_product = request.airavata_client.getDataProduct(
                request.authz_token, dataset.original_data_product_uri
            )
            return data_product.productName
        except Exception:
            return "N/A"


class DatasetSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        write_only=True,
        required=False,
        help_text="Required when creating a new Dataset",
    )
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=True)
    owner = serializers.SlugRelatedField(slug_field='username', read_only=True)
    data_product_uri = serializers.CharField(read_only=True)
    original_data_product_uri = serializers.CharField(read_only=True)
    description = serializers.CharField(
        style={"base_template": "textarea.html"}, allow_blank=True
    )
    original_filename = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    original_url = serializers.SerializerMethodField()
    simccs_project = SimccsProjectPrimaryKeyRelatedField()
    userIsProjectOwner = serializers.SerializerMethodField()
    versions = DatasetVersionSerializer(many=True, read_only=True)
    current_version = serializers.SlugRelatedField(slug_field='version', read_only=True)
    userHasWriteAccess = serializers.SerializerMethodField()

    class Meta:
        model = models.Dataset
        fields = "__all__"
        validators = []

    @transaction.atomic
    def create(self, validated_data):
        file = validated_data.pop("file")
        request = self.context["request"]
        dataset = models.Dataset.objects.create(
            **validated_data,
            owner=request.user,
        )
        current_version = self._create_dataset_version(dataset, file)
        dataset.current_version = current_version
        dataset.save()
        return dataset

    @transaction.atomic
    def update(self, instance, validated_data):
        file = validated_data.pop("file", None)
        if file is not None:
            current_version = self._create_dataset_version(instance, file)
            instance.current_version = current_version
        instance.name = validated_data["name"]
        instance.description = validated_data["description"]
        instance.save()
        return instance

    def _create_dataset_version(self, dataset, file):
        request = self.context["request"]
        project_dir = os.path.join(
            "ProjectData",
            f"Project-{dataset.simccs_project.id}")
        original_data_product = user_storage.save(
            request, project_dir, file, name=file.name, content_type=file.content_type
        )
        dataset_version = models.DatasetVersion.objects.create(
            version=(dataset.current_version.version +
                     1 if dataset.current_version else 1),
            original_data_product_uri=original_data_product.productUri,
            dataset=dataset)
        try:
            transformed_file = self._transform_file(
                user_storage.open_file(request, original_data_product),
                dataset_type=dataset.type,
                content_type=file.content_type
            )
        except Exception as e:
            logger.exception(f"Failed to transform file {file.name}")
            raise serializers.ValidationError(
                {'file': [f'Failed to transform file to GeoJSON: {e}']})
        if transformed_file:
            data_product = user_storage.save(
                request,
                project_dir,
                transformed_file,
                name=transformed_file.name,
                content_type="application/geo+json",
            )
            dataset_version.data_product_uri = data_product.productUri
            dataset_version.save()
        return dataset_version

    def _transform_file(self, input_file, dataset_type, content_type):
        # transform the file and return the transformed file (GeoJSON)
        if content_type.startswith("text/"):
            return self._transform_text_file(input_file, dataset_type)
        else:
            raise Exception(
                f"Unrecognized file type {content_type}. File must be a plain text tab delimited file.")

    def _transform_text_file(self, input_file, dataset_type):
        # assume the delimiter is "tab"
        rawdata = pd.read_csv(input_file, sep="\t", index_col=False)
        rawdata.rename(columns=partial(self._map_column_names, dataset_type=dataset_type), inplace=True)
        self._verify_all_columns_exist(rawdata, dataset_type)
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

    def _map_column_names(self, name, dataset_type):
        """Convert column names to standard names."""
        if name.lower().startswith("id"):
            return "ID"
        elif name.lower().startswith("costfix"):
            return "costFix ($M)"
        elif name.lower().startswith("fixo&m") or name.lower().startswith("fixom"):
            # Source files want "fixO&M ($M/y)" but sink files want "fixO&M ($M/yr)"
            if dataset_type == 'source':
                return "fixO&M ($M/y)"
            else:
                return "fixO&M ($M/yr)"
        elif name.lower().startswith("varo&m") or name.lower().startswith("varom"):
            return "varO&M ($/tCO2)"
        elif name.lower().startswith("capmax"):
            return "capMax (MtCO2/y)"
        elif name.lower().startswith("lon"):
            return "LON"
        elif name.lower().startswith("lat"):
            return "LAT"
        elif name.lower().startswith("fieldcap"):
            return "fieldCap (MtCO2)"
        elif name.lower().startswith("wellcap"):
            return "wellCap (MtCO2/yr)"
        elif name.lower().startswith("wellcostfix"):
            return "wellCostFix ($M)"
        elif name.lower().startswith("wellfixo&m") or name.lower().startswith("wellfixom"):
            return "wellFixO&M ($M/yr)"
        elif name.lower().startswith("sink_id"):
            return "Sink_ID"
        elif name.lower().startswith("name"):
            # Source files want "NAME" but sink files want "Name"
            if dataset_type == 'source':
                return "NAME"
            else:
                return "Name"
        else:
            return name

    def _verify_all_columns_exist(self, df, dataset_type):

        if dataset_type == 'source':
            expected_columns = ['ID',
                                'costFix ($M)',
                                'fixO&M ($M/y)',
                                'varO&M ($/tCO2)',
                                'capMax (MtCO2/y)',
                                'N/A',
                                'LON',
                                'LAT',
                                'NAME']
        elif dataset_type == 'sink':
            expected_columns = ['ID',
                                'Sink_ID',
                                'fieldCap (MtCO2)',
                                'costFix ($M)',
                                'fixO&M ($M/yr)',
                                'wellCap (MtCO2/yr)',
                                'wellCostFix ($M)',
                                'wellFixO&M ($M/yr)',
                                'varO&M ($/tCO2)',
                                'LON',
                                'LAT',
                                'Name']
        for expected_column in expected_columns:
            if expected_column not in df:
                raise Exception(
                    f"Missing column '{expected_column}' in {dataset_type} file")

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
        if dataset.data_product_uri:
            return sdk_urls.get_download_url(dataset.data_product_uri)
        else:
            return None

    def get_original_url(self, dataset):
        return sdk_urls.get_download_url(dataset.original_data_product_uri)

    def get_userIsProjectOwner(self, instance):
        return self.context['request'].user == instance.simccs_project.owner

    def validate(self, attrs):
        data = super().validate(attrs)
        queryset = models.Dataset.objects.filter(
            simccs_project_id=data['simccs_project'], name=data['name'])
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                {'name': ["This project already has a dataset with that name."]})
        return data

    def get_userHasWriteAccess(self, instance):
        return self.context['request'].user == instance.owner


class MaptoolDataSerializer(serializers.ModelSerializer):
    bbox = BboxField(required=False, allow_null=True)
    popup = CSVField(required=False, allow_null=True)

    class Meta:
        model = models.MaptoolData
        fields = ["bbox", "style", "dataset", "popup", "symbol"]


class MaptoolConfigSerializer(serializers.ModelSerializer):
    data = MaptoolDataSerializer(many=True, allow_null=True)
    bbox = BboxField(required=False, allow_null=True)

    class Meta:
        model = models.MaptoolConfig
        fields = ["bbox", "data"]


class CaseSerializer(serializers.ModelSerializer):
    maptool = MaptoolConfigSerializer(required=True, allow_null=True)
    owner = serializers.SlugRelatedField(slug_field='username', read_only=True)
    title = serializers.CharField(required=True)
    description = serializers.CharField(
        style={"base_template": "textarea.html"}, allow_blank=True
    )
    datasets = serializers.SerializerMethodField()
    userHasWriteAccess = serializers.SerializerMethodField()
    simccs_project = SimccsProjectPrimaryKeyRelatedField()
    userIsProjectOwner = serializers.SerializerMethodField()
    airavata_project = serializers.SerializerMethodField()
    useable = serializers.SerializerMethodField(
        help_text="Whether this case can be used to create scenarios")

    class Meta:
        model = models.Case
        fields = "__all__"
        validators = []

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

    def get_airavata_project(self, instance):
        return instance.simccs_project.airavata_project

    def get_useable(self, instance):
        """Returns True if case has at least one source and one sink dataset."""
        has_source = False
        has_sink = False
        for datum in instance.maptool.data.all():
            if datum.dataset.type == 'source':
                has_source = True
            elif datum.dataset.type == 'sink':
                has_sink = True
        return has_source and has_sink

    def validate(self, attrs):
        data = super().validate(attrs)
        queryset = models.Case.objects.filter(
            simccs_project_id=data['simccs_project'], title=data['title'])
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                {'title': ["This project already has a case with that title."]})
        return data


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
    dataset_versions = DatasetVersionSerializer(many=True, read_only=True)

    class Meta:
        model = models.ScenarioExperiment
        fields = ('experiment_id', 'parameters', 'dataset_versions')

    def to_representation(self, instance):
        request = self.context['request']
        result = super().to_representation(instance)
        result['experiment_url'] = reverse(
            "django_airavata_workspace:view_experiment", args=[instance.experiment_id])
        result['experiment_result'] = reverse(
            "simccs_maptool:experiment-result", args=[instance.experiment_id])
        result['solution_summary'] = reverse(
            "simccs_maptool:solution-summary", args=[instance.experiment_id])
        result['experiment_download_url'] = reverse(
            "airavata_django_portal_sdk:download_experiment_dir", args=[
                instance.experiment_id])
        try:
            experiment = request.airavata_client.getExperiment(
                request.authz_token, instance.experiment_id)
            result['experiment_name'] = experiment.experimentName
            result['experiment_state'] = ExperimentState._VALUES_TO_NAMES[
                experiment.experimentStatus[-1].state]
        except Exception as e:
            logger.warning(f"Failed to load experiment from API: {e}")
        return result


class ScenarioSerializer(serializers.ModelSerializer):
    parameters = ParametersSerializer()
    sources = ScenarioSourceSerializer(many=True)
    sinks = ScenarioSinkSerializer(many=True)
    experiments = ScenarioExperimentSerializer(many=True)

    class Meta:
        model = models.Scenario
        fields = ("title",
                  "scenario_id",
                  "sources",
                  "sinks",
                  "experiments",
                  "parameters")


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field='username', read_only=True)
    description = serializers.CharField(
        style={"base_template": "textarea.html"}, allow_blank=True
    )
    scenarios = ScenarioSerializer(many=True)

    class Meta:
        model = models.Workspace
        fields = (
            "id",
            "name",
            "description",
            "owner",
            "scenarios",
            "case",
            "created",
            "updated")

    @transaction.atomic
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
            if models.Scenario.objects.filter(workspace=workspace,
                                              title=scenario['title']).exists():
                raise serializers.ValidationError(
                    {'title': 'A scenario with that title already exists in the workspace.'})
            if models.Scenario.objects.filter(
                    workspace=workspace, scenario_id=scenario['scenario_id']).exists():
                raise serializers.ValidationError(
                    {'scenario_id': 'A scenario with that scenario_id already exists in the workspace.'})
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
                # capture the current version of the datasets used in the scenario
                dataset_versions = set()
                for source in scenario_inst.sources.all():
                    dataset_versions.add(source.dataset.current_version)
                for sink in scenario_inst.sinks.all():
                    dataset_versions.add(sink.dataset.current_version)
                experiment_inst.dataset_versions.set(dataset_versions)
                experiment_inst.save()
                for parameter in experiment_parameters:
                    models.ScenarioExperimentParameter.objects.create(
                        experiment=experiment_inst, **parameter
                    )
        return workspace

    @transaction.atomic
    def update(self, instance, validated_data):
        logger.debug(f"workspace update {validated_data}")
        scenarios = validated_data.pop("scenarios")
        for scenario in scenarios:
            sources = scenario.pop("sources")
            sinks = scenario.pop("sinks")
            experiments = scenario.pop("experiments")
            parameters = scenario.pop("parameters")
            scenario_id = scenario.pop("scenario_id")
            logger.debug(f"scenario={scenario}")
            if models.Scenario.objects.exclude(
                    scenario_id=scenario_id).filter(
                    workspace=instance,
                    title=scenario['title']).exists():
                raise serializers.ValidationError(
                    {'title': 'A scenario with that title already exists in the workspace.'})
            scenario_inst, created = models.Scenario.objects.update_or_create(
                workspace=instance, scenario_id=scenario_id, defaults=scenario)
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
                # if created, also capture the current version of the datasets
                # used in the scenario
                if created:
                    dataset_versions = set()
                    for source in scenario_inst.sources.all():
                        dataset_versions.add(source.dataset.current_version)
                    for sink in scenario_inst.sinks.all():
                        dataset_versions.add(sink.dataset.current_version)
                    experiment_inst.dataset_versions.set(dataset_versions)
                    experiment_inst.save()
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

    def validate(self, attrs):
        data = super().validate(attrs)
        request = self.context['request']
        queryset = models.Workspace.objects.filter(
            case_id=data['case'], owner=request.user, name=data['name'])
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                {'name': ["You already have a workspace with that name for this case."]})
        return data
