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
      <b-table :items="datasetItems">
        <template #cell(actions)="">
          <b-button variant="primary">Edit</b-button>
          <b-button variant="danger">Delete</b-button>
        </template>
      </b-table>
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
      <b-table :items="caseItems">
        <template #cell(actions)="">
          <b-button variant="primary">Use</b-button>
          <b-button variant="primary">Edit</b-button>
          <b-button variant="danger">Delete</b-button>
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
            actions: null,
          };
        });
      }
    },
    caseItems() {
      if (!this.cases) {
        return [];
      } else {
        return this.cases.map((aCase) => {
          return {
            title: aCase.title,
            description: aCase.description,
            actions: null,
          };
        });
      }
    },
  },
};
</script>

<style></style>
