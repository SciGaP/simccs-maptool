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
      utils.FetchUtils.post("/maptool/api/projects/", newProject)
        .then((result) => {
          // TODO: add a success message
          this.$router.push({
            name: "project",
            params: { projectId: result.id },
          });
        })
        .catch((e) => {
          if (e.details && e.details.response) {
            this.serverValidationErrors = e.details.response;
          }
          // TODO: display some sort of error message for unexpected error
        });
    },
  },
};
</script>

<style></style>
