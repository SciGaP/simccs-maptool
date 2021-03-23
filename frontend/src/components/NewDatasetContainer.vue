<template>
  <b-card :title="title">
    <b-form @submit="onSubmit">
      <b-form-group label="Name" label-class="required">
        <b-form-input
          v-model="$v.dataset.name.$model"
          :state="validateState($v.dataset.name)"
          required
        ></b-form-input>
        <b-form-invalid-feedback v-if="!$v.dataset.name.required"
          >This field is required.</b-form-invalid-feedback
        >
        <b-form-invalid-feedback v-if="!$v.dataset.name.serverValidation">{{
          this.serverValidation.name.join(" ")
        }}</b-form-invalid-feedback>
      </b-form-group>
      <b-form-group label="Description">
        <b-form-input v-model="dataset.description"></b-form-input>
      </b-form-group>
      <b-form-group label="Type" label-class="required">
        <b-form-select
          v-model="dataset.type"
          :options="typeOptions"
          required
        ></b-form-select>
      </b-form-group>
      <b-form-group label="File" label-class="required">
        <b-form-file
          v-model="$v.dataset.file.$model"
          :state="validateState($v.dataset.file)"
          required
        />
        <b-form-invalid-feedback v-if="!$v.dataset.file.required"
          >A file is required.</b-form-invalid-feedback
        >
        <b-form-invalid-feedback v-if="!$v.dataset.file.serverValidation">{{
          this.serverValidation.file.join(" ")
        }}</b-form-invalid-feedback>
      </b-form-group>
      <b-button type="submit" variant="primary" :disabled="$v.$invalid"
        >Submit</b-button
      >
    </b-form>
  </b-card>
</template>

<script>
const { utils } = AiravataAPI;
import { validationMixin } from "vuelidate";
import { required } from "vuelidate/lib/validators";
import validateFromServer from "../validators/validateFromServer";
import { validateState } from "../validators/formHelpers";

export default {
  mixins: [validationMixin],
  name: "new-dataset-container",
  props: {
    projectId: {
      type: [String, Number],
      required: true,
    },
  },
  data() {
    return {
      dataset: {
        name: "",
        type: "source",
        description: "",
        file: null,
        simccs_project: this.projectId,
      },
      serverValidation: null,
      submittedData: null,
    };
  },
  validations() {
    return {
      dataset: {
        name: {
          required,
          serverValidation: validateFromServer(
            () => (this.submittedData ? this.submittedData.get("name") : null),
            () => (this.serverValidation ? this.serverValidation.name : null)
          ),
        },
        type: {
          required,
        },
        file: {
          required,
          serverValidation: validateFromServer(
            () => (this.submittedData ? this.submittedData.get("file") : null),
            () => (this.serverValidation ? this.serverValidation.file : null)
          ),
        },
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
      utils.FetchUtils.post("/maptool/api/datasets/", formData)
        .then(() => {
          // TODO: add a success message
          this.$router.push({
            name: "project",
            params: { projectId: this.projectId },
          });
        })
        .catch((e) => {
          this.submittedData = formData;
          if (e.details.response) {
            this.serverValidation = e.details.response;
          }
          // TODO else display some error message for unexpected error
        });
    },
    validateState,
  },
};
</script>

<style scoped>
.b-form-file.is-invalid ~ .invalid-feedback {
  display: block;
}
</style>
