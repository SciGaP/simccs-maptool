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

    class Meta:
        model = models.SimccsProject
        fields = ("id", "name", "owner", "group", "airavata_project", "new_owner")

    def create(self, validated_data):
        request = self.context["request"]
        simccs_project = models.SimccsProject.objects.create(
            owner=request.user, **validated_data)
        # create an airavata project for this SimCCS project and store its ID
        airavata_project = Project(
            owner=request.user.username,
            gatewayId=settings.GATEWAY_ID,
            name="simccs:" + validated_data["name"])
        airavata_project_id = request.airavata_client.createProject(
            request.authz_token, settings.GATEWAY_ID, airavata_project)
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
