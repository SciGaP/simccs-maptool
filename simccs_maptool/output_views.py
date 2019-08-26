from urllib.parse import quote
from django.urls import reverse


class SolutionLinkProvider:
    display_type = "link"
    immediate = True
    name = "Solution Link"

    def generate_data(self, request, experiment_output, experiment, output_file=None):
        return {
            "label": "Analyze in MapTool",
            "url": reverse("simccs_maptool:home")
            + "?experiment_id="
            + quote(experiment.experimentId),
        }
