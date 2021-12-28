<template>
  <b-table
    :items="items"
    :fields="fields"
    sort-by="experiment_created"
    sort-desc
    small
    class="mt-2"
  >
    <template #cell(checked)="data">
      <b-form-checkbox
        v-model="checkedExperiments"
        :value="data.item.experiment_id"
        :disabled="!selectableExperimentIds.includes(data.item.experiment_id)"
        @input="experimentChecked"
      >
      </b-form-checkbox>
    </template>
    <template #cell(experiment_name)="data">
      <small>{{ data.value }}</small>
      <br />
      <small class="text-muted">
        {{ scenarioExperimentMapping[data.item.experiment_id].title }}</small
      >
      <br />
      <small class="text-muted"
        >{{ data.item.parameters.Project_Period }} yr -
        {{ data.item.parameters.Capture_Target }} Mt/yr</small
      >
    </template>

    <template #cell(case)="data">
      <small>{{ data.value }}</small>
    </template>

    <template #cell(experiment_created)="data">
      <small>{{ data.value }}</small>
      <br />
      <small class="text-muted"
        >by
        <b>{{
          workspaceExperimentMapping[data.item.experiment_id].owner
        }}</b></small
      >
    </template>

    <template #head(actions)="data">
      <template v-if="checkedExperiments.length > 0">
        <b-button
          @click="downloadCheckedExperiments"
          size="sm"
          class="btn-block"
          variant="primary"
          ><i class="fas fa-download"></i> .shp (for selected)</b-button
        >
      </template>
      <template v-else>
        {{ data.label }}
      </template>
    </template>
    <template #head(checked)="">
      <b-form-checkbox v-model="selectAll" @change="selectAllChanged">
      </b-form-checkbox>
    </template>
    <template #cell(actions)="data">
      <b-button
        v-if="
          selectableExperimentIds.includes(data.item.experiment_id) &&
          checkedExperiments.length === 0
        "
        @click="downloadExperiments([data.item.experiment_id])"
        size="sm"
        class="btn-block"
        variant="primary"
        ><i class="fas fa-download"></i> .shp</b-button
      >
      <b-button size="sm" @click="data.toggleDetails" class="mr-2 btn-block">
        {{ data.detailsShowing ? "Hide" : "Show" }} Notes
        <b-badge variant="light"
          >{{ data.item.notes.length }}
          <span class="sr-only">notes count</span></b-badge
        >
      </b-button>
    </template>
    <template #row-details="row">
      <b-card v-for="note in row.item.notes" :key="note.id">
        {{ note.note_text }}
        <template #footer>
          <small
            >On
            {{
              new Date(note.created).toLocaleString("en-US", {
                dateStyle: "short",
                timeStyle: "short",
              })
            }}
            by <b>{{ note.owner }}</b></small
          >
        </template>
      </b-card>
      <b-card>
        <b-textarea v-model="row.item.new_note" class="mb-2" />
        <b-button size="sm" @click="addNote(row.item)" variant="primary"
          >Add Note</b-button
        >
      </b-card>
    </template>
  </b-table>
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
  data() {
    return {
      workspaces: null,
      checkedExperiments: [],
      selectAll: false,
      cases: [],
    };
  },
  created() {
    this.fetchData();
  },
  methods: {
    async fetchData() {
      this.workspaces = await utils.FetchUtils.get(
        `/maptool/api/workspaces/?project=${encodeURIComponent(this.projectId)}`
      );

      const caseIds = [...new Set(this.workspaces.map((w) => w.case))];
      this.cases = await Promise.all(
        caseIds.map((caseId) =>
          utils.FetchUtils.get(`/maptool/api/cases/${caseId}/`)
        )
      );
    },
    async downloadExperiments(experimentIds) {
      // fetch experiment-result to force generation of shapefiles
      const experimentsWithResults = [];
      const requests = experimentIds.map((expId) => {
        const experiment = this.experiments.find(
          (exp) => exp.experiment_id === expId
        );
        if (experiment) {
          experimentsWithResults.push(experiment);
          return utils.FetchUtils.get(experiment["experiment_result"]);
        } else {
          console.log("Could not find experiment " + expId);
          return Promise.resolve();
        }
      });
      await Promise.all(requests);
      const resp = await AiravataAPI.utils.FetchUtils.post(
        "/sdk/download-experiments/",
        {
          experiments: experimentsWithResults.map((experiment) => {
            const scenario = this.scenarioExperimentMapping[
              experiment.experiment_id
            ];
            return {
              experiment_id: experiment.experiment_id,
              path: "shapeFiles",
              includes: [
                {
                  pattern: "Network.*",
                  rename: `${scenario.title}_solution_network_${experiment["experiment_name"]}$ext`,
                },
                {
                  pattern: "Sources.*",
                  rename: `${scenario.title}_sources_${experiment["experiment_name"]}$ext`,
                },
                {
                  pattern: "Sinks.*",
                  rename: `${scenario.title}_sinks_${experiment["experiment_name"]}$ext`,
                },
              ],
            };
          }),
        }
      );
      window.location.assign(resp.download_url);
    },
    async downloadCheckedExperiments() {
      await this.downloadExperiments(this.checkedExperiments);
    },
    selectAllChanged(value) {
      console.log("selectAllChanged", value);
      if (this.selectAll) {
        this.checkedExperiments = [...this.selectableExperimentIds];
      } else {
        this.checkedExperiments = [];
      }
    },
    experimentChecked() {
      if (
        this.selectAll &&
        this.checkedExperiments.length < this.selectableExperimentIds.length
      ) {
        this.selectAll = false;
      }
    },
    async addNote(rowItem) {
      const response = await utils.FetchUtils.post("/maptool/api/notes/", {
        note_text: rowItem.new_note,
        experiment: rowItem.id,
      });
      rowItem.new_note = null;
      rowItem.notes.push(response);
    },
  },
  computed: {
    experiments() {
      if (this.workspaces && this.workspaces.length > 0) {
        const experiments = [];
        for (const workspace of this.workspaces) {
          for (const scenario of workspace.scenarios) {
            experiments.push(...scenario.experiments);
          }
        }
        return experiments;
      } else {
        return [];
      }
    },
    scenarioExperimentMapping() {
      const mapping = {};
      if (this.workspaces && this.workspaces.length > 0) {
        for (const workspace of this.workspaces) {
          for (const scenario of workspace.scenarios) {
            for (const experiment of scenario.experiments) {
              mapping[experiment.experiment_id] = scenario;
            }
          }
        }
      }
      return mapping;
    },
    workspaceExperimentMapping() {
      const mapping = {};
      if (this.workspaces && this.workspaces.length > 0) {
        for (const workspace of this.workspaces) {
          for (const scenario of workspace.scenarios) {
            for (const experiment of scenario.experiments) {
              mapping[experiment.experiment_id] = workspace;
            }
          }
        }
      }
      return mapping;
    },
    caseExperimentMapping() {
      const mapping = {};
      if (
        this.workspaces &&
        this.workspaces.length > 0 &&
        this.cases &&
        this.cases.length > 0
      ) {
        for (const workspace of this.workspaces) {
          for (const scenario of workspace.scenarios) {
            for (const experiment of scenario.experiments) {
              mapping[experiment.experiment_id] = this.cases.find(
                (c) => c.id === workspace.case
              );
            }
          }
        }
      }
      return mapping;
    },
    fields() {
      return [
        { key: "checked", label: "" },
        { key: "experiment_name", label: "Name" },
        {
          key: "case",
          sortable: true,
          sortByFormatted: true,
          formatter: (value, key, item) => {
            return this.caseExperimentMapping[item.experiment_id]?.title;
          },
        },
        {
          key: "experiment_created",
          label: "Created",
          formatter: (value) =>
            new Date(value).toLocaleString("en-US", {
              dateStyle: "short",
              timeStyle: "short",
            }),
          sortable: true,
        },
        {
          key: "experiment_state",
          label: "Status",
        },
        "actions",
      ];
    },
    items() {
      return this.experiments;
    },
    selectableExperimentIds() {
      return this.experiments
        .filter((exp) => exp.experiment_result)
        .map((exp) => exp.experiment_id);
    },
  },
  watch: {
    projectId: "fetchData",
  },
};
</script>
