<template>
  <b-card no-body v-if="dataset">
    <b-card-body>
      <b-card-title>Dataset: {{ dataset.name }} </b-card-title>
      <b-card-sub-title>
        <dataset-type-badge :type="dataset.type" />
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
      <b-button variant="primary" :to="{ name: 'dataset', params: { id: id } }">
        <i class="fa fa-edit" aria-hidden="true"></i>
        Edit</b-button
      >
      <b-button
        variant="secondary"
        :to="{ name: 'project-datasets', params: { projectId } }"
      >
        Back</b-button
      >
    </b-card-body>
  </b-card>
</template>

<script>
import DatasetTypeBadge from "./DatasetTypeBadge.vue";
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
  components: { DatasetTypeBadge },
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
      result.forEach((v) => {
        const date = new Date(v.created);
        v.created = date.toLocaleString("en-US", {
          dateStyle: "short",
          timeStyle: "short",
        });
      });
      return result;
    },
    fields() {
      return [
        "version",
        "original_filename",
        { key: "url", label: "GeoJSON" },
        "created",
      ];
    },
  },
  data() {
    return {
      dataset: null,
    };
  },
};
</script>
