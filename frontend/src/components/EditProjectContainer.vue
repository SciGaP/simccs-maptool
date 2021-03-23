<template>
  <project-editor
    v-if="project"
    :value="project"
    :serverValidationErrors="serverValidationErrors"
    @submit="onSubmit"
    @transferOwnership="onTransferOwnership"
  />
</template>

<script>
import ProjectEditor from "./ProjectEditor.vue";

const { utils } = AiravataAPI;
export default {
  components: { ProjectEditor },
  props: {
    projectId: {
      type: [String, Number],
      required: true,
    },
  },
  data() {
    return {
      project: null,
      serverValidationErrors: null,
    };
  },
  created() {
    utils.FetchUtils.get(
      `/maptool/api/projects/${encodeURIComponent(this.projectId)}/`
    ).then((project) => {
      this.project = project;
    });
  },
  methods: {
    onSubmit(updatedProject) {
      utils.FetchUtils.put(
        `/maptool/api/projects/${encodeURIComponent(this.projectId)}/`,
        updatedProject
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
    onTransferOwnership(updatedProject, newOwner) {
      const url = `/maptool/api/projects/${encodeURIComponent(
        this.projectId
      )}/`;
      // First update the project, then transfer ownership
      utils.FetchUtils.put(url, updatedProject)
        .then((project) => {
          project.new_owner = newOwner;
          return utils.FetchUtils.post(url + "transfer_ownership/", project);
        })
        .then(() => {
          // TODO: add a success message
          this.$router.push({
            name: "project",
            params: { projectId: this.projectId },
          });
        });
      // TODO: handle failure
    },
  },
};
</script>
