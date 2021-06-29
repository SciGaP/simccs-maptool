<template>
  <div>
    <b-alert show class="mt-2"
      >Your copy will be created when you click the <b>Save</b> button.</b-alert
    >
    <case-editor
      v-if="aCase"
      :value="aCase"
      :server-validation-errors="serverValidationErrors"
      @submit="onSubmit"
    />
  </div>
</template>

<script>
import CaseEditor from "./CaseEditor.vue";

const { utils } = AiravataAPI;
export default {
  components: { CaseEditor },
  props: {
    projectId: {
      type: [String, Number],
      required: true,
    },
    id: {
      type: [String, Number],
      required: true,
    },
  },
  data() {
    return {
      aCase: null,
      serverValidationErrors: null,
    };
  },
  created() {
    utils.FetchUtils.get(
      `/maptool/api/cases/${encodeURIComponent(this.id)}/`
    ).then((aCase) => {
      this.aCase = aCase;
      this.aCase.title = "Copy of " + this.aCase.title;
    });
  },
  methods: {
    onSubmit(newCase) {
      // reset any validation errors
      this.serverValidationErrors = null;
      utils.FetchUtils.post("/maptool/api/cases/", newCase)
        .then(() => {
          // TODO: add a success message
          this.$router.push({
            name: "project",
            params: { projectId: this.projectId },
          });
        })
        .catch((e) => {
          if (e.details && e.details.response) {
            this.serverValidationErrors = e.details.response;
          }
          // TODO: else: display some sort of error message for unexpected error
        });
    },
  },
};
</script>
