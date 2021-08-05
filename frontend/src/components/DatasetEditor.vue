<template>
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
        :disabled="isEditing || typeDisabled"
        required
      ></b-form-select>
    </b-form-group>
    <b-form-group
      label="File"
      :label-class="isFileRequired ? ['required'] : []"
    >
      <b-form-file
        v-model="$v.dataset.file.$model"
        :state="validateState($v.dataset.file)"
        :required="isFileRequired"
      />
      <b-form-invalid-feedback
        v-if="'required' in $v.dataset.file && !$v.dataset.file.required"
        >A file is required.</b-form-invalid-feedback
      >
      <b-form-invalid-feedback v-if="!$v.dataset.file.serverValidation">{{
        this.serverValidationErrors.file.join(" ")
      }}</b-form-invalid-feedback>
      <template #description>
        Please use the
        <a
          href="/static/simccs_maptool/SimCCS_Gateway_Sources_and_Sinks_Template.xlsx"
          >Excel template</a
        >
        to create your source and sink dataset files, then "save as" each
        worksheet as tab delimited text.
      </template>
    </b-form-group>
    <b-button type="submit" variant="primary" :disabled="$v.$invalid"
      >Save</b-button
    >
    <b-button v-if="isEditing" type="button" variant="danger" @click="onDelete">
      Delete</b-button
    >
  </b-form>
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
    typeDisabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      dataset: this.cloneValue(),
      submittedData: null,
    };
  },
  validations() {
    const validations = {
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
    if (this.isFileRequired) {
      validations.dataset.file.required = required;
    }
    return validations;
  },
  computed: {
    typeOptions() {
      return [
        { value: "source", text: "Source" },
        { value: "sink", text: "Sink" },
        { value: "costsurface", text: "Cost Surface", disabled: true },
      ];
    },
    isEditing() {
      return "id" in this.dataset;
    },
    isFileRequired() {
      return !this.isEditing;
    },
  },
  methods: {
    onSubmit(event) {
      event.preventDefault();
      const formData = new FormData();
      for (const name in this.dataset) {
        if (Object.prototype.hasOwnProperty.call(this.dataset, name)) {
          const value = this.dataset[name];
          if (name === "file" && !value) {
            continue;
          }
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
  watch: {
    dataset() {
      this.dataset = this.cloneValue();
    },
  },
};
</script>

<style scoped>
.b-form-file.is-invalid ~ .invalid-feedback {
  display: block;
}
</style>
