<template>
  <div>
    <notifications-display />
    <div class="row">
      <div class="col-auto">
        <h1 class="h3 mb-0">Project: {{ name }}</h1>
        <div class="text-muted mb-2">
          <small
            >Owned by <b>{{ project && project.owner }}</b></small
          >
          <small v-if="projectGroup"
            >, shared with group <b>{{ projectGroup.name }}</b></small
          >
        </div>
      </div>
      <div class="col-auto" v-if="project && project.userHasWriteAccess">
        <b-button to="edit" variant="primary" class="ml-2 text-nowrap"
          ><i class="fa fa-edit" aria-hidden="true"></i> Edit Project</b-button
        >
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

const { NotificationsDisplay } = window.CommonUI || {};

export default {
  props: {
    projectId: {
      type: [String, Number],
      required: true,
    },
  },
  components: {
    NotificationsDisplay,
  },
  data() {
    return {
      project: null,
      projects: null,
      projectGroup: null,
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
              text: `${p.owner} / ${p.name}`,
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
        if (project.group) {
          this.fetchProjectGroup();
        }
      });
    },
    fetchProjectGroup() {
      utils.FetchUtils.get(
        `/api/groups/${encodeURIComponent(this.project.group)}/`
      ).then((group) => {
        this.projectGroup = group;
      });
    },
  },
  watch: {
    $route: "fetchProject",
  },
};
</script>

<style></style>
