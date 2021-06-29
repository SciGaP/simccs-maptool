<template>
  <b-modal ref="modal" :title="title" hide-footer>
    <dataset-editor
      :value="dataset"
      :server-validation-errors="serverValidationErrors"
      :type-disabled="true"
      @submit="onSubmit"
    />
  </b-modal>
</template>

<script>
const { errors, utils } = AiravataAPI;
import { validationMixin } from "vuelidate";
import { validateState } from "../validators/formHelpers";
import DatasetEditor from "./DatasetEditor.vue";

export default {
  mixins: [validationMixin],
  props: {
    projectId: {
      type: [String, Number],
      required: true,
    },
    datasetType: {
      type: String,
      default: "source",
    },
  },
  components: {
    DatasetEditor,
  },
  data() {
    return {
      dataset: null,
      serverValidationErrors: null,
    };
  },
  computed: {
    title() {
      return `Create a new ${this.datasetType}`;
    },
  },
  methods: {
    onSubmit(formData) {
      utils.FetchUtils.post("/maptool/api/datasets/", formData, "", {
        ignoreErrors: true,
      })
        .then((dataset) => {
          this.$emit("created", dataset);
          this.hide();
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
    show() {
      this.$refs["modal"].show();
      // reset form
      this.dataset = {
        name: "",
        type: this.datasetType,
        description: "",
        file: null,
        simccs_project: this.projectId,
      };
    },
    hide() {
      this.$refs["modal"].hide();
    },
  },
  watch: {
    datasetType() {
      if (this.dataset) {
        this.dataset.type = this.datasetType;
      }
    },
  },
};
</script>
