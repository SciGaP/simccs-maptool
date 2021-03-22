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
        <template #description>
          Select a group of users to share this project with. Or
          <b-link href="/groups/create/" target="_blank"
            >create a new group</b-link
          >
          and then
          <b-link @click="refreshGroups">refresh the list of groups</b-link> to
          select it.
        </template>
        <b-input-group>
          <b-form-select v-model="project.group" :options="groupOptions">
            <template #first>
              <b-form-select-option :value="null"
                >-- Select a group --</b-form-select-option
              >
            </template>
          </b-form-select>
          <b-input-group-append>
            <b-button
              variant="outline-secondary"
              :href="`/groups/edit/${encodeURIComponent(
                selectedGroup && selectedGroup.id
              )}/`"
              target="_blank"
              :disabled="!selectedGroupEditable"
              >Edit</b-button
            >
            <b-button
              variant="outline-secondary"
              @click="viewMembers"
              :disabled="!selectedGroup"
              >View Members</b-button
            >
          </b-input-group-append>
        </b-input-group>
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
        <b-modal
          ref="view-members-modal"
          :title="`Members of group ${selectedGroup && selectedGroup.name}`"
          ok-only
        >
          <ul class="group-members-list">
            <li v-for="member in selectedGroupMembers" :key="member">
              {{ member }}
            </li>
          </ul>
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
              text: this.formatGroupOptionText(g),
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
      return this.selectedGroupMembers.filter((m) => m !== this.project.owner);
    },
    selectedGroupMembers() {
      return this.selectedGroup
        ? this.selectedGroup.members.map(this.stripDomainFromGroupUser)
        : [];
    },
    selectedGroupEditable() {
      return (
        this.selectedGroup &&
        (this.selectedGroup.isOwner || this.selectedGroup.isAdmin)
      );
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
    formatGroupOptionText(group) {
      return `${group.name} - created by ${this.stripDomainFromGroupUser(
        group.ownerId
      )}, ${group.members.length} members`;
    },
    stripDomainFromGroupUser(userId) {
      return userId.slice(0, userId.lastIndexOf("@"));
    },
    viewMembers() {
      this.$refs["view-members-modal"].show();
    },
    refreshGroups() {
      this.loadGroups();
    },
  },
};
</script>

<style scoped>
.group-members-list {
  max-height: 50vh;
  overflow: auto;
}
</style>
