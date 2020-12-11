<template>
  <b-card :title="title">
    <b-form @submit="onSubmit">
      <b-form-group label="Name">
        <b-form-input v-model="dataset.name" required></b-form-input>
      </b-form-group>
      <b-form-group label="Description">
        <b-form-input v-model="dataset.description"></b-form-input>
      </b-form-group>
      <b-form-group label="Type">
        <b-form-select
          v-model="dataset.type"
          :options="typeOptions"
          required
        ></b-form-select>
      </b-form-group>
      <b-form-group label="File">
        <b-form-file v-model="dataset.file" required />
      </b-form-group>
      <b-button type="submit" variant="primary">Submit</b-button>
    </b-form>
  </b-card>
</template>

<script>
const { utils } = AiravataAPI;

export default {
  name: "new-dataset-container",
  data() {
    return {
      dataset: {
        type: "source",
        description: ""
      },
    };
  },
  computed: {
    typeOptions() {
      return [
        { value: "source", text: "Source" },
        { value: "sink", text: "Sink" },
        { value: "costsurface", text: "Cost Surface", disabled: true },
      ];
    },
    title() {
      return this.dataset.name ? this.dataset.name : "New Dataset";
    },
  },
  methods: {
    onSubmit(event) {
      event.preventDefault();
      const formData = new FormData();
      for (const name in this.dataset) {
        if (Object.prototype.hasOwnProperty.call(this.dataset, name)) {
          const value = this.dataset[name];
          formData.append(name, value);
        }
      }
      utils.FetchUtils.post("/maptool/api/datasets/", formData).then(() => {
        // TODO: add a success message
        this.$router.push({ path: "/" });
      });
    },
  },
};
</script>

<style></style>
