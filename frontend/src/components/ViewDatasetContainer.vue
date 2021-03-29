<template>
  <b-card no-body v-if="dataset">
    <b-card-body>
      <b-card-title>Dataset: {{ dataset.name }} </b-card-title>
      <b-card-sub-title>
        <dataset-badge :type="dataset.type" />
      </b-card-sub-title>
      <b-table :items="versions" :fields="fields" class="mt-2">
        <template #cell(version)="data">
          {{ data.value }}
          <b-badge
            v-if="data.value == dataset.current_version"
            variant="primary"
            >current</b-badge
          >
        </template>
        <template #cell(original_filename)="data">
          <a :href="data.item.original_url">{{ data.value }}</a>
        </template>
        <template #cell(url)="data">
          <a v-if="data.value" :href="data.value">Download</a>
        </template>
      </b-table>
    </b-card-body>
  </b-card>
</template>

<script>
import DatasetBadge from "./DatasetBadge.vue";
const { utils } = AiravataAPI;

export default {
  props: {
    id: {
      type: [String, Number],
      required: true,
    },
    projectId: {
      type: [String, Number],
      required: true,
    },
  },
  components: { DatasetBadge },
  created() {
    utils.FetchUtils.get(
      `/maptool/api/datasets/${encodeURIComponent(this.id)}/`
    ).then((dataset) => {
      this.dataset = dataset;
    });
  },
  computed: {
    versions() {
      const result = this.dataset ? this.dataset.versions : [];
      result.sort((a, b) => b.version - a.version);
      return result;
    },
    fields() {
      return ["version", "original_filename", { key: "url", label: "GeoJSON" }];
    },
  },
  data() {
    return {
      dataset: null,
    };
  },
};
</script>
