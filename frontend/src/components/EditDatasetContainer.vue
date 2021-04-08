<template>
  <dataset-editor
    v-if="dataset"
    :value="dataset"
    :server-validation-errors="serverValidationErrors"
    @submit="onSubmit"
    @delete="onDelete"
  />
</template>

<script>
const { utils } = AiravataAPI;
import { validationMixin } from "vuelidate";
import { validateState } from "../validators/formHelpers";
import DatasetEditor from "./DatasetEditor.vue";

export default {
  mixins: [validationMixin],
  name: "new-dataset-container",
  props: {
    id: {
      type: [String, Number],
      required: true,
    },
    projectId: {
      type: [String, Number],
      required: true,
    },
  },
  components: {
    DatasetEditor,
  },
  created() {
    utils.FetchUtils.get(
      `/maptool/api/datasets/${encodeURIComponent(this.id)}/`
    ).then((dataset) => {
      this.dataset = dataset;
    });
  },
  data() {
    return {
      dataset: null,
      serverValidationErrors: null,
    };
  },
  methods: {
    onSubmit(formData) {
      utils.FetchUtils.put(
        `/maptool/api/datasets/${encodeURIComponent(this.id)}/`,
        formData,
        { ignoreErrors: true }
      )
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
    onDelete() {
      utils.FetchUtils.delete(
        `/maptool/api/datasets/${encodeURIComponent(this.id)}/`
      ).then(() => {
        this.$router.push({
          name: "project",
          params: { projectId: this.projectId },
        });
      });
    },
    validateState,
  },
};
</script>
