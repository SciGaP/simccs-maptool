<template>
  <b-table :items="workspaces" :fields="fields" sort-by="updated" :sort-desc="true" small borderless>
    <template #cell(name)="data">
      <b-link :href="`/maptool/build?workspace=${data.item.id}`">{{
        data.value
      }}</b-link>
    </template>
    <template #cell(updated)="data">
      {{
        new Date(data.value).toLocaleString("en-US", {
          dateStyle: "short",
          timeStyle: "short",
        })
      }}
    </template>
    <template #cell(scenarios)="data">
      {{ data.value.length }}
    </template>
    <template #cell(experiments)="data">
      {{
        data.item.scenarios.reduce(
          (acc, item) => acc + item.experiments.length,
          0
        )
      }}
    </template>
  </b-table>
</template>

<script>
export default {
  props: ["workspaces"],
  computed: {
    fields() {
      return ["name", "updated", "scenarios", "experiments"];
    },
  },
};
</script>

<style></style>
