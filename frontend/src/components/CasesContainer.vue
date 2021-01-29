<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Datasets</h1>
      </div>
      <div class="col-auto">
        <b-button to="/datasets/new" variant="primary"
          ><i class="fa fa-plus" aria-hidden="true"></i> New Dataset</b-button
        >
      </div>
    </div>
    <b-card>
      <b-table :items="datasetItems"></b-table>
    </b-card>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Cases</h1>
      </div>
      <div class="col-auto">
        <b-button to="/cases/new" variant="primary"
          ><i class="fa fa-plus" aria-hidden="true"></i> New Case</b-button
        >
      </div>
    </div>
    <b-card>
      <b-table :items="caseItems" :fields="caseFields">
        <template #cell(actions)="data">
          <b-link
            class="btn btn-secondary"
            role="button"
            :href="`/maptool/build/?case=${data.item.id}`"
          >
            <i class="fa fa-map" aria-hidden="true"></i>
            Use</b-link
          >
          <b-button
            variant="primary"
            :to="{ name: 'case', params: { id: data.item.id } }"
            v-if="data.item.userHasWriteAccess"
          >
            <i class="fa fa-edit" aria-hidden="true"></i>
            Edit</b-button
          >
        </template>
      </b-table>
    </b-card>
  </div>
</template>

<script>
const { utils } = AiravataAPI;
export default {
  name: "cases-container",
  data() {
    return {
      datasets: null,
      cases: null,
    };
  },
  created() {
    utils.FetchUtils.get("/maptool/api/datasets/").then((datasets) => {
      this.datasets = datasets;
    });
    utils.FetchUtils.get("/maptool/api/cases/").then((cases) => {
      this.cases = cases;
    });
  },
  computed: {
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
            actions: null,
          };
        });
      }
    },
  },
};
</script>

<style></style>
