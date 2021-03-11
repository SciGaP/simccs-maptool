<template>
  <b-card :title="cardTitle">
    <b-form @submit="onSubmit">
      <b-form-group label="Name" label-class="required">
        <b-form-input
          v-model="$v.project.name.$model"
          :state="validateState($v.project.name)"
          required
        ></b-form-input>
        <b-form-invalid-feedback v-if="!$v.project.name.required"
          >This field is required.</b-form-invalid-feedback
        >
      </b-form-group>

      <b-form-group
        label="Group"
        description="Share this project with a group."
      >
        <b-form-select v-model="project.group" :options="groupOptions">
          <template #first>
            <b-form-select-option :value="null"
              >-- Select a group --</b-form-select-option
            >
          </template>
        </b-form-select>
      </b-form-group>
      <div>
        <b-button type="submit" variant="primary" :disabled="$v.$invalid"
          >Save</b-button
        >
        <b-button
          type="button"
          variant="secondary"
          v-if="project.id"
          :disabled="!transferOwnershipButtonEnabled"
          @click="showTransferOwnershipModal"
          >Transfer Ownership</b-button
        >
        <b-modal
          ref="transfer-ownership-modal"
          title="Transfer Ownership"
          @ok="okClicked"
          ok-title="Save"
          :ok-disabled="!newOwner"
        >
          <b-form-select v-model="newOwner" :options="newOwnerOptions">
            <template #first>
              <b-form-select-option :value="null" disabled
                >-- Select a new project owner --</b-form-select-option
              >
            </template>
          </b-form-select>
        </b-modal>
      </div>
    </b-form>
  </b-card>
</template>

<script>
import { validationMixin } from "vuelidate";
import { required } from "vuelidate/lib/validators";
import { validateState } from "../validators/formHelpers";
const { services } = AiravataAPI;

export default {
  mixins: [validationMixin],
  props: {
    value: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      project: JSON.parse(JSON.stringify(this.value)), // clone the value prop
      groups: null,
      newOwner: null,
    };
  },
  created() {
    this.loadGroups();
  },
  computed: {
    cardTitle() {
      return `Project: ${this.project.name}`;
    },
    groupOptions() {
      return this.groups
        ? this.groups.map((g) => {
            return {
              value: g.id,
              text: g.name,
            };
          })
        : [];
    },
    transferOwnershipButtonEnabled() {
      // A group must be selected before ownership can be transfered
      return !this.$v.$invalid && this.project.group;
    },
    selectedGroup() {
      return this.project.group && this.groups
        ? this.groups.find((g) => g.id === this.project.group)
        : null;
    },
    newOwnerOptions() {
      return this.selectedGroup
        ? this.selectedGroup.members
            .map((m) => m.slice(0, m.lastIndexOf("@")))
            .filter((m) => m !== this.project.owner)
        : [];
    },
  },
  validations() {
    return {
      project: {
        name: {
          required,
        },
      },
    };
  },
  methods: {
    validateState,
    onSubmit(event) {
      event.preventDefault();
      this.$emit("submit", this.project);
    },
    loadGroups() {
      services.GroupService.list().then(
        (groups) => (this.groups = groups.results.filter((g) => g.isMember))
      );
    },
    showTransferOwnershipModal() {
      this.$refs["transfer-ownership-modal"].show();
    },
    okClicked() {
      this.$emit("transferOwnership", this.project, this.newOwner);
    },
  },
};
</script>

<style></style>
