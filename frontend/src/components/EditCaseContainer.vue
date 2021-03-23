<template>
  <case-editor
    v-if="aCase"
    :value="aCase"
    :serverValidationErrors="serverValidationErrors"
    @submit="onSubmit"
  />
</template>

<script>
import CaseEditor from "./CaseEditor.vue";

const { utils } = AiravataAPI;
export default {
  components: { CaseEditor },
  name: "edit-case-container",
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
    });
  },
  methods: {
    onSubmit(updatedCase) {
      utils.FetchUtils.put(
        `/maptool/api/cases/${encodeURIComponent(this.id)}/`,
        updatedCase
      )
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
        });
    },
  },
};
</script>
