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
          {{ data.value }}
          <div class="text-muted">
            <small>{{ data.item.description }}</small>
          </div>
        </template>
        <template #cell(type)="data">
          <b-badge v-if="data.value === 'source'" variant="success"
            ><i class="fa fa-arrow-circle-up" aria-hidden="true"></i>
            Source</b-badge
          >
          <b-badge v-else-if="data.value === 'sink'" variant="danger"
            ><i class="fa fa-arrow-circle-down" aria-hidden="true"></i>
            Sink</b-badge
          >
        </template>
        <template #cell(filename)="data">
          <a :href="data.item.original_url">{{ data.value }}</a>
        </template>
        <template #cell(url)="data">
          <a v-if="data.value" :href="data.value">Download</a>
        </template>
      </b-table>
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
const { utils } = AiravataAPI;
export default {
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
      cases: null,
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
  },
  computed: {
    datasetFields() {
      return ["name", "type", "filename", { key: "url", label: "GeoJSON" }];
    },
    datasetItems() {
      if (!this.datasets) {
        return [];
      } else {
        return this.datasets.map((ds) => {
          return {
            name: ds.name,
            description: ds.description,
            type: ds.type,
            filename: ds.original_filename,
            original_url: ds.original_url,
            url: ds.url,
            // actions: null,
          };
        });
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
