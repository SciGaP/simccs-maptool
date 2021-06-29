<template>
  <div></div>
</template>

<script>
const { utils } = AiravataAPI;

export default {
  created() {
    utils.FetchUtils.get(`/maptool/api/projects/`).then((projects) => {
      if (projects.length > 0) {
        let defaultProject = projects.find((p) => p.userMostRecentProject);
        if (!defaultProject) {
          // if there isn't a most recent project for the user, just pick the first one
          defaultProject = projects[0];
        }
        this.$router.push({
          name: "project",
          params: { projectId: defaultProject.id },
        });
      } else {
        // create a default project
        utils.FetchUtils.post(`/maptool/api/projects/`, {
          name: "Default",
        }).then((project) => {
          this.$router.push({
            name: "project",
            params: { projectId: project.id },
          });
        });
      }
    });
  },
};
</script>

<style></style>
