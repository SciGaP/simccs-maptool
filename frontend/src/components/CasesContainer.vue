<template>
  <b-card>
    <b-tabs>
      <b-tab title="Cases">
        <div class="row my-2">
          <div class="ml-auto col-auto">
            <b-button to="cases/new" variant="primary"
              ><i class="fa fa-plus" aria-hidden="true"></i> New Case</b-button
            >
          </div>
        </div>
        <b-table :items="caseItems" :fields="caseFields">
          <template #cell(title)="data">
            <span class="text-break">{{ data.value }}</span>
            <div class="text-muted">
              <small>{{ data.item.description }}</small>
            </div>
          </template>
          <template #cell(actions)="data">
            <b-button
              variant="secondary"
              :to="{ name: 'case', params: { id: data.item.id } }"
              v-if="data.item.userHasWriteAccess"
            >
              <i class="fa fa-edit" aria-hidden="true"></i>
              Edit</b-button
            >
            <b-button
              variant="secondary"
              :to="{ name: 'case-copy', params: { id: data.item.id } }"
              v-if="!data.item.userHasWriteAccess"
            >
              <i class="fa fa-copy" aria-hidden="true"></i>
              Copy</b-button
            >
            <b-button
              variant="warning"
              @click="claimCase(data.item.id)"
              title="Claim ownership of this case"
              v-if="
                !data.item.userHasWriteAccess && data.item.userIsProjectOwner
              "
            >
              <i class="fa fa-hand-paper" aria-hidden="true"></i>
              Claim
            </b-button>
          </template>
          <template #row-details="row">
            <b-card
              class="my-workspaces-card"
              :title="`My ${row.item.title} Workspaces`"
              title-tag="h6"
              v-if="getWorkspacesForCase(row.item).length > 0"
            >
              <my-workspaces :workspaces="getWorkspacesForCase(row.item)" />
              <b-button
                @click="newWorkspace(row.item)"
                variant="primary"
                :title="`Create new workspace using the ${row.item.title} case`"
              >
                <i class="fa fa-map" aria-hidden="true"></i>
                New Workspace</b-button
              >
            </b-card>
            <b-button
              v-else
              @click="newWorkspace(row.item)"
              variant="primary"
              :title="`Create new workspace using the ${row.item.title} case`"
            >
              <i class="fa fa-map" aria-hidden="true"></i>
              Create New Workspace</b-button
            >
          </template>
        </b-table>
      </b-tab>
      <b-tab title="Datasets">
        <div class="row my-2">
          <div class="ml-auto col-auto">
            <b-button to="datasets/new" variant="primary"
              ><i class="fa fa-plus" aria-hidden="true"></i> New
              Dataset</b-button
            >
          </div>
        </div>
        <b-table :items="datasetItems" :fields="datasetFields">
          <template #cell(name)="data">
            <span class="text-break">{{ data.value }}</span>
            <div class="text-muted">
              <small>{{ data.item.description }}</small>
            </div>
          </template>
          <template #cell(type)="data">
            <dataset-type-badge :type="data.value" />
          </template>
          <template #cell(original_filename)="data" style="max-width: 20%">
            <a
              class="text-break"
              :href="data.item.original_url"
              target="_blank"
              >{{ data.value }}</a
            >
            <br />
            <small
              ><a v-if="data.item.url" :href="data.item.url" target="_blank"
                >Download GeoJSON</a
              ></small
            >
          </template>
          <template #cell(actions)="data">
            <b-button
              variant="secondary"
              :to="{ name: 'dataset', params: { id: data.item.id } }"
              v-if="data.item.userHasWriteAccess && !data.item.deleted"
            >
              <i class="fa fa-edit" aria-hidden="true"></i>
              Edit</b-button
            >
            <b-button
              variant="secondary"
              v-if="data.item.userHasWriteAccess && data.item.deleted"
              @click="undeleteDataset(data.item.id)"
            >
              <i class="fa fa-trash-restore" aria-hidden="true"></i>
              Undelete</b-button
            >
          </template>
          <template #cell(updated)="data">
            {{
              new Date(data.value).toLocaleString("en-US", {
                dateStyle: "short",
                timeStyle: "short",
              })
            }}
            <br />
            <small v-if="!data.item.deleted"
              ><b-link
                :to="{ name: 'dataset-view', params: { id: data.item.id } }"
                class="text-muted"
              >
                {{ data.item.versions.length }} version{{
                  data.item.versions.length > 1 ? "s" : ""
                }}
              </b-link></small
            >
          </template>
        </b-table>
        <small v-if="deletedDatasets && deletedDatasets.length > 0">
          <b-link
            class="text-muted"
            @click="showDeletedDatasets = !showDeletedDatasets"
          >
            {{
              showDeletedDatasets
                ? "Hide deleted datasets"
                : `Show ${deletedDatasets.length} deleted dataset${
                    deletedDatasets.length > 1 ? "s" : ""
                  }`
            }}
          </b-link>
        </small>
      </b-tab>
    </b-tabs>
  </b-card>
</template>

<script>
import DatasetTypeBadge from "./DatasetTypeBadge.vue";
import MyWorkspaces from "./MyWorkspaces.vue";
const { session, utils } = AiravataAPI;
export default {
  components: { DatasetTypeBadge, MyWorkspaces },
  name: "cases-container",
  props: {
    projectId: {
      type: [String, Number],
      required: true,
    },
  },
  data() {
    return {
      datasets: null,
      deletedDatasets: null,
      cases: null,
      showDeletedDatasets: false,
      userWorkspaces: null,
    };
  },
  created() {
    this.fetchData();
  },
  methods: {
    fetchData() {
      utils.FetchUtils.get(
        `/maptool/api/datasets/?project=${encodeURIComponent(this.projectId)}`
      ).then((datasets) => {
        this.datasets = datasets;
      });
      utils.FetchUtils.get(
        `/maptool/api/datasets/list_deleted/?project=${encodeURIComponent(
          this.projectId
        )}`
      ).then((datasets) => {
        this.deletedDatasets = datasets;
        if (this.deletedDatasets.length === 0) {
          this.showDeletedDatasets = false;
        }
      });
      utils.FetchUtils.get(
        `/maptool/api/cases/?project=${encodeURIComponent(this.projectId)}`
      ).then((cases) => {
        this.cases = cases;
      });
      utils.FetchUtils.get(
        `/maptool/api/workspaces/?project=${encodeURIComponent(
          this.projectId
        )}&owner=${encodeURIComponent(session.Session.username)}`
      ).then((workspaces) => {
        this.userWorkspaces = workspaces;
      });
    },
    claimCase(caseId) {
      utils.FetchUtils.post(
        `/maptool/api/cases/${caseId}/claim_ownership/`
      ).then(this.fetchData);
      // TODO: handle failure
    },
    undeleteDataset(datasetId) {
      const url = `/maptool/api/datasets/${datasetId}/undelete/`;
      utils.FetchUtils.put(url, {}).then(this.fetchData);
    },
    getWorkspacesForCase(aCase) {
      if (this.userWorkspaces) {
        return this.userWorkspaces.filter((w) => w.case === aCase.id);
      } else {
        return [];
      }
    },
    newWorkspace(aCase) {
      const workspace = {
        name: `Workspace for ${aCase.title}, ${new Date().toLocaleString(
          "en-US",
          {
            dateStyle: "short",
            timeStyle: "short",
          }
        )}`,
        description: "",
        case: aCase.id,
        scenarios: [],
      };
      utils.FetchUtils.post("/maptool/api/workspaces/", workspace).then(
        (ws) => {
          window.location = `/maptool/build?workspace=${ws.id}`;
        }
      );
    },
  },
  computed: {
    datasetFields() {
      return [
        "name",
        { key: "type", sortable: true },
        { key: "original_filename", label: "Filename" },
        { key: "updated", sortable: true },
        "actions",
      ];
    },
    datasetItems() {
      if (this.datasets && this.deletedDatasets) {
        return this.showDeletedDatasets ? this.deletedDatasets : this.datasets;
      } else {
        return [];
      }
    },
    caseFields() {
      return ["title", "owner", "actions"];
    },
    caseItems() {
      if (!this.cases) {
        return [];
      } else {
        return this.cases.map((aCase) => {
          return {
            id: aCase.id,
            title: aCase.title,
            description: aCase.description,
            owner: aCase.owner,
            userHasWriteAccess: aCase.userHasWriteAccess,
            userIsProjectOwner: aCase.userIsProjectOwner,
            actions: null,
            _showDetails: true,
          };
        });
      }
    },
  },
  watch: {
    projectId: "fetchData",
  },
};
</script>

<style scoped>
.my-workspaces-card {
  margin-bottom: 0px;
}
</style>
