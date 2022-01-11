# Generated by Django 2.2.17 on 2021-12-27 15:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('simccs_maptool', '0018_auto_20210706_0845'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScenarioExperimentNote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note_text', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='simccs_maptool.ScenarioExperiment')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]