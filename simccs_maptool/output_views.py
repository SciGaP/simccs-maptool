from urllib.parse import quote
from django.urls import reverse


class SolutionLinkProvider:
    display_type = "link"

    def generate_data(self, experiment_output, experiment, output_file=None):
        return {
            "label": "Analyze in MapTool",
            "url": reverse("simccs_maptool:home")
            + "?experiment_id="
            + quote(experiment.experimentId),
        }
