<template>
  <project-editor v-if="project" :value="project" @submit="onSubmit" />
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
      ).then(() => {
        // TODO: add a success message
        this.$router.push({
          name: "project",
          params: { projectId: this.projectId },
        });
      });
    },
  },
};
</script>
