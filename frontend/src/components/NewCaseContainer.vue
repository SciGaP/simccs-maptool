<template>
  <case-editor
    :value="aCase"
    :server-validation-errors="serverValidationErrors"
    @submit="onSubmit"
  />
</template>

<script>
import CaseEditor from "./CaseEditor.vue";

const { errors, utils } = AiravataAPI;
export default {
  components: { CaseEditor },
  name: "new-case-container",
  props: {
    projectId: {
      type: [String, Number],
      required: true,
    },
  },
  data() {
    return {
      aCase: {
        title: "",
        description: "",
        maptool: {
          bbox: null,
          data: [],
        },
        simccs_project: this.projectId,
      },
      serverValidationErrors: null,
    };
  },
  methods: {
    onSubmit(newCase) {
      // reset any validation errors
      this.serverValidationErrors = null;
      utils.FetchUtils.post("/maptool/api/cases/", newCase, "", {
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
  },
};
</script>
