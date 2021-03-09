<template>
  <div></div>
</template>

<script>
const { utils } = AiravataAPI;

export default {
  created() {
    utils.FetchUtils.get(`/maptool/api/projects/`).then((projects) => {
      if (projects.length > 0) {
        this.$router.push({
          name: "project",
          params: { projectId: projects[0].id },
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
