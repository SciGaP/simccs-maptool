<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Datasets</h1>
      </div>
      <div class="col-auto">
        <b-button to="datasets/new" variant="primary"
          ><i class="fa fa-plus" aria-hidden="true"></i> New Dataset</b-button
        >
      </div>
    </div>
    <b-card>
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
    </b-card>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Cases</h1>
      </div>
      <div class="col-auto">
        <b-button to="cases/new" variant="primary"
          ><i class="fa fa-plus" aria-hidden="true"></i> New Case</b-button
        >
      </div>
    </div>
    <b-card>
      <b-table :items="caseItems" :fields="caseFields">
        <template #cell(actions)="data">
          <b-link
            class="btn btn-primary"
            role="button"
            :href="`/maptool/build?case=${data.item.id}`"
          >
            <i class="fa fa-map" aria-hidden="true"></i>
            Use</b-link
          >
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
            v-if="!data.item.userHasWriteAccess && data.item.userIsProjectOwner"
          >
            <i class="fa fa-hand-paper" aria-hidden="true"></i>
            Claim
          </b-button>
        </template>
      </b-table>
    </b-card>
  </div>
</template>

<script>
import DatasetTypeBadge from "./DatasetTypeBadge.vue";
const { utils } = AiravataAPI;
export default {
  components: { DatasetTypeBadge },
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
      return ["title", "description", "owner", "actions"];
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

<style></style>
