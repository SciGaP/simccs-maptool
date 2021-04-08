<template>
  <project-editor
    :value="project"
    :serverValidationErrors="serverValidationErrors"
    @submit="onSubmit"
  />
</template>

<script>
import ProjectEditor from "./ProjectEditor.vue";
const { utils } = AiravataAPI;
export default {
  components: { ProjectEditor },

  data() {
    return {
      project: {
        name: "New Project",
        group: null,
      },
      serverValidationErrors: null,
    };
  },
  methods: {
    onSubmit(newProject) {
      utils.FetchUtils.post("/maptool/api/projects/", newProject, "", {
        ignoreErrors: true,
      })
        .then((result) => {
          // TODO: add a success message
          this.$router.push({
            name: "project",
            params: { projectId: result.id },
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

<style></style>
