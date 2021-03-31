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
          this.serverValidationErrors.name.join(" ")
        }}</b-form-invalid-feedback>
      </b-form-group>
      <b-form-group label="Description">
        <b-form-input v-model="dataset.description"></b-form-input>
      </b-form-group>
      <b-form-group label="Type" label-class="required">
        <b-form-select
          v-model="dataset.type"
          :options="typeOptions"
          :disabled="isEditing"
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
          this.serverValidationErrors.file.join(" ")
        }}</b-form-invalid-feedback>
      </b-form-group>
      <b-button type="submit" variant="primary" :disabled="$v.$invalid"
        >Save</b-button
      >
      <b-button
        v-if="isEditing"
        type="button"
        variant="danger"
        @click="onDelete"
      >
        Delete</b-button
      >
    </b-form>
  </b-card>
</template>

<script>
import { validationMixin } from "vuelidate";
import { required } from "vuelidate/lib/validators";
import validateFromServer from "../validators/validateFromServer";
import { validateState } from "../validators/formHelpers";

export default {
  mixins: [validationMixin],
  props: {
    value: {
      type: Object,
      required: true,
    },
    // parent component should pass in any server side validation errors that
    // occur on submission
    serverValidationErrors: {
      type: Object,
    },
  },
  data() {
    return {
      dataset: this.cloneValue(),
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
            () =>
              this.serverValidationErrors
                ? this.serverValidationErrors.name
                : null
          ),
        },
        type: {
          required,
        },
        file: {
          required,
          serverValidation: validateFromServer(
            () => (this.submittedData ? this.submittedData.get("file") : null),
            () =>
              this.serverValidationErrors
                ? this.serverValidationErrors.file
                : null
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
    isEditing() {
      return "id" in this.dataset;
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
      this.submittedData = formData;
      this.$emit("submit", formData);
    },
    validateState,
    cloneValue() {
      const result = JSON.parse(JSON.stringify(this.value));
      result.file = null;
      return result;
    },
    onDelete() {
      this.$emit("delete");
    },
  },
};
</script>

<style scoped>
.b-form-file.is-invalid ~ .invalid-feedback {
  display: block;
}
</style>
