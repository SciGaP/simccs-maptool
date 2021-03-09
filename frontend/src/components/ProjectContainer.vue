<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h3 mb-3">Project: {{ name }}</h1>
      </div>
      <div class="col-auto ml-auto d-flex align-items-start">
        <b-form-select
          :options="projectOptions"
          :value="projectId"
          @change="onProjectChanged"
        >
          <template #first>
            <b-form-select-option :value="null" disabled
              >-- Select a project --</b-form-select-option
            >
          </template>
        </b-form-select>
        <b-button to="/projects/new" variant="primary" class="ml-2 text-nowrap"
          ><i class="fa fa-plus" aria-hidden="true"></i> New Project</b-button
        >
      </div>
    </div>

    <router-view :project-id="projectId"></router-view>
  </div>
</template>

<script>
const { utils } = AiravataAPI;
export default {
  props: {
    projectId: {
      type: [String, Number],
      required: true,
    },
  },
  components: {},
  data() {
    return {
      project: null,
      projects: null,
    };
  },
  created() {
    this.fetchProject();
    utils.FetchUtils.get(`/maptool/api/projects/`).then((projects) => {
      this.projects = projects;
    });
  },
  computed: {
    name() {
      return this.project ? this.project.name : "";
    },
    projectOptions() {
      return this.projects
        ? this.projects.map((p) => {
            return {
              text: p.name,
              value: p.id,
            };
          })
        : [];
    },
  },
  methods: {
    onProjectChanged(value) {
      this.$router.push({
        name: "project",
        params: { projectId: value },
      });
    },
    fetchProject() {
      utils.FetchUtils.get(
        `/maptool/api/projects/${encodeURIComponent(this.projectId)}/`
      ).then((project) => {
        this.project = project;
      });
    },
  },
  watch: {
    $route: "fetchProject",
  },
};
</script>

<style></style>
