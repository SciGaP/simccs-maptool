import logging

from airavata_django_portal_sdk import user_storage
from rest_framework import serializers

from simccs_maptool import models

logger = logging.getLogger(__name__)


class DatasetSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        write_only=True,
        required=False,
        help_text="Required when creating a new Dataset",
    )
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    data_product_uri = serializers.CharField(read_only=True)
    original_data_product_uri = serializers.CharField(read_only=True)
    description = serializers.CharField(
        style={"base_template": "textarea.html"}, allow_blank=True
    )

    class Meta:
        model = models.Dataset
        fields = "__all__"

    def create(self, validated_data):
        file = validated_data.pop("file")
        logger.debug(f"file={file}")
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
            validated_data["type"],
        )
        if transformed_file:
            data_product = user_storage.save(
                request, "Datasets", transformed_file, name=transformed_file.name
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

    def _transform_file(self, input_file, dataset_type):
        # TODO: transform the file and return the transformed file
        pass


class MaptoolDataSerializer(serializers.ModelSerializer):
    dataset = serializers.PrimaryKeyRelatedField(queryset=models.Dataset.objects.all())

    class Meta:
        model = models.MaptoolData
        fields = ["bbox", "style", "dataset"]


class MaptoolConfigSerializer(serializers.ModelSerializer):
    data = MaptoolDataSerializer(many=True, allow_null=True)

    class Meta:
        model = models.MaptoolConfig
        fields = ["bbox", "data"]


class CaseSerializer(serializers.ModelSerializer):
    maptool = MaptoolConfigSerializer(required=True, allow_null=True)
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    group = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(
        style={"base_template": "textarea.html"}, allow_blank=True
    )

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
        # TODO: add/remove/update MaptoolConfig.data entries
        # TODO: update MaptoolConfig
        # update Case - description, group, title
        instance.description = validated_data["description"]
        instance.title = validated_data["title"]
        instance.group = validated_data["group"]
        instance.save()
        return instance
