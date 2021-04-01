# Generated by Django 2.2.17 on 2021-03-29 09:20

from django.db import migrations


def migrate_to_dataset_versions(apps, schema_editor):
    "Create a dataset version 1 for each dataset"
    Dataset = apps.get_model("simccs_maptool", "Dataset")
    for dataset in Dataset.objects.all():
        current_version = dataset.versions.create(
            version=1,
            data_product_uri=dataset.data_product_uri,
            original_data_product_uri=dataset.original_data_product_uri)
        dataset.current_version = current_version
        dataset.save()


class Migration(migrations.Migration):

    dependencies = [
        ('simccs_maptool', '0013_auto_20210329_0919'),
    ]

    operations = [
        migrations.RunPython(migrate_to_dataset_versions, migrations.RunPython.noop)
    ]