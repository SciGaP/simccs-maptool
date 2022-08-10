<template>
  <div>
    <notifications-display />
    <project-editor
      v-if="project"
      :value="project"
      :serverValidationErrors="serverValidationErrors"
      @submit="onSubmit"
      @transferOwnership="onTransferOwnership"
    />
  </div>
</template>

<script>
import ProjectEditor from "./ProjectEditor.vue";

const { errors, utils } = AiravataAPI;
const { NotificationsDisplay } = window.CommonUI || {};
export default {
  components: { ProjectEditor, NotificationsDisplay },
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
        updatedProject,
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
