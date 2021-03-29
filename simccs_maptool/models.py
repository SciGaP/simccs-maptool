from django.conf import settings
from django.core import validators
from django.db import models
from django.db.models import Q

# 4 comma separated floating point numbers
bbox_validator = validators.RegexValidator(regex=r"^-?\d+(\.\d+)?(,-?\d+(\.\d+)?){3}$")
csv_validator = validators.RegexValidator(regex=r"^[^,]+(,[^,])+$")


def get_user_group_membership_ids(request):
    "Return group ids for all groups that user is a member of"
    # query for the groups that the user belongs to
    group_manager_client = request.profile_service['group_manager']
    group_memberships = group_manager_client.getAllGroupsUserBelongs(
        request.authz_token, request.user.username + "@" + settings.GATEWAY_ID)
    group_ids = [group.id for group in group_memberships]
    return group_ids


class SimccsProject(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.CharField(max_length=64, null=True)
    # FIXME: technically airavata_project should not be nullable, but project was
    # introduced after cases and datasets and so the migration needed a default
    # project to assign the cases and datasets
    airavata_project = models.CharField(max_length=255, null=True)

    @staticmethod
    def filter_by_user(request):
        "Filter by owner or current user is member of project's group"
        group_ids = get_user_group_membership_ids(request)
        # return SimccsProjects where the current user is a member of the
        # project's group or the owner
        return SimccsProject.objects.filter(
            Q(owner=request.user) | Q(group__in=group_ids))

    class Meta:
        unique_together = ["owner", "name"]


class Case(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    simccs_project = models.ForeignKey(SimccsProject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["simccs_project", "title"]


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
    simccs_project = models.ForeignKey(SimccsProject, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    current_version = models.ForeignKey(
        'DatasetVersion', on_delete=models.PROTECT, null=True, related_name="+")

    class Meta:
        unique_together = ["simccs_project", "name"]

    @property
    def data_product_uri(self):
        return self.current_version.data_product_uri

    @property
    def original_data_product_uri(self):
        return self.current_version.original_data_product_uri


class DatasetVersion(models.Model):

    # incrementing version number for a given dataset
    version = models.IntegerField(default=1)
    data_product_uri = models.CharField(max_length=64)
    original_data_product_uri = models.CharField(max_length=64)
    created = models.DateTimeField(auto_now_add=True)
    dataset = models.ForeignKey(Dataset,
                                on_delete=models.CASCADE,
                                related_name="versions")

    class Meta:
        unique_together = ['dataset', 'version']


class MaptoolConfig(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name="maptool")
    bbox = models.CharField(max_length=128, null=True, validators=[bbox_validator])


class MaptoolData(models.Model):
    maptool_config = models.ForeignKey(
        MaptoolConfig, on_delete=models.CASCADE, related_name="data"
    )
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    style = models.TextField(null=True)
    bbox = models.CharField(max_length=128, null=True, validators=[bbox_validator])
    popup = models.CharField(max_length=128, null=True, validators=[csv_validator])


class Workspace(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['case', 'owner', 'name']


class Scenario(models.Model):
    title = models.CharField(max_length=255)
    scenario_id = models.CharField(max_length=255)
    workspace = models.ForeignKey(Workspace,
                                  on_delete=models.CASCADE,
                                  related_name="scenarios")

    class Meta:
        unique_together = [['workspace', 'title'], ['workspace', 'scenario_id']]


class ScenarioParameter(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    scenario = models.ForeignKey(Scenario,
                                 on_delete=models.CASCADE,
                                 related_name="parameters")

    class Meta:
        unique_together = ['scenario', 'name']


class ScenarioSource(models.Model):
    source_id = models.CharField(max_length=255)
    scenario = models.ForeignKey(Scenario,
                                 on_delete=models.CASCADE,
                                 related_name="sources")
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    # TODO: source fields, or should we derive these from the dataset geojson?

    class Meta:
        unique_together = ['scenario', 'dataset', 'source_id']


class ScenarioSink(models.Model):
    sink_id = models.CharField(max_length=255)
    scenario = models.ForeignKey(Scenario,
                                 on_delete=models.CASCADE,
                                 related_name="sinks")
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    # TODO: sink fields, or should we derive these from the dataset geojson?

    class Meta:
        unique_together = ['scenario', 'dataset', 'sink_id']


class ScenarioExperiment(models.Model):
    experiment_id = models.CharField(max_length=255, unique=True)
    scenario = models.ForeignKey(Scenario,
                                 on_delete=models.CASCADE,
                                 related_name="experiments")


class ScenarioExperimentParameter(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    experiment = models.ForeignKey(ScenarioExperiment,
                                   on_delete=models.CASCADE,
                                   related_name="parameters")

    class Meta:
        unique_together = ['experiment', 'name']


class UserPreference(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ['user', 'name']
