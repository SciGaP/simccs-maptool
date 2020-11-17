from django.conf import settings
from django.core import validators
from django.db import models

# 4 comma separated floating point numbers
bbox_validator = validators.RegexValidator(regex=r"^-?\d+(\.\d+)?(,-?\d+(\.\d+)?){3}$")


class Case(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.CharField(max_length=64, null=True)


class Dataset(models.Model):
    TYPE_CHOICES = (
        ("sink", "Sink"),
        ("source", "Source"),
        ("costsurface", "Cost Surface"),
    )

    name = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    data_product_uri = models.CharField(max_length=64)
    original_data_product_uri = models.CharField(max_length=64)


class MaptoolConfig(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='maptool')
    bbox = models.CharField(max_length=128, null=True, validators=[bbox_validator])


class MaptoolData(models.Model):
    maptool_config = models.ForeignKey(MaptoolConfig, on_delete=models.CASCADE, related_name="data")
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    style = models.TextField(null=True)
    bbox = models.CharField(max_length=128, null=True, validators=[bbox_validator])