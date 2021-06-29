<template>
  <b-card title="New Dataset">
    <dataset-editor
      :value="dataset"
      :server-validation-errors="serverValidationErrors"
      @submit="onSubmit"
    />
  </b-card>
</template>

<script>
const { errors, utils } = AiravataAPI;
import { validationMixin } from "vuelidate";
import { validateState } from "../validators/formHelpers";
import DatasetEditor from "./DatasetEditor.vue";

export default {
  mixins: [validationMixin],
  name: "new-dataset-container",
  props: {
    projectId: {
      type: [String, Number],
      required: true,
    },
  },
  components: {
    DatasetEditor,
  },
  data() {
    return {
      dataset: {
        name: "",
        type: "source",
        description: "",
        file: null,
        simccs_project: this.projectId,
      },
      serverValidationErrors: null,
    };
  },
  methods: {
    onSubmit(formData) {
      utils.FetchUtils.post("/maptool/api/datasets/", formData, "", {
        ignoreErrors: true,
      })
        .then(() => {
          // TODO: add a success message
          this.$router.push({
            name: "project",
            params: { projectId: this.projectId },
          });
        })
        .catch((e) => {
          if (errors.ErrorUtils.isValidationError(e)) {
            this.serverValidationErrors = e.details.response;
          } else {
            // otherwise it is some unexpected error
            utils.FetchUtils.reportError(e);
          }
        });
    },
    validateState,
  },
};
</script>
