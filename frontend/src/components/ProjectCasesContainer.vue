<template>
  <div>
    <div class="row my-2">
      <div class="ml-auto col-auto">
        <b-button to="cases/new" variant="primary"
          ><i class="fa fa-plus" aria-hidden="true"></i> New Case</b-button
        >
      </div>
    </div>
    <b-table :items="caseItems" :fields="caseFields">
      <template #cell(title)="data">
        <span class="text-break">{{ data.value }}</span>
        <div class="text-muted">
          <small>{{ data.item.description }}</small>
        </div>
      </template>
      <template #cell(actions)="data">
        <b-button
          variant="secondary"
          :to="{ name: 'case', params: { id: data.item.id } }"
          v-if="data.item.userHasWriteAccess"
        >
          <i class="fa fa-edit" aria-hidden="true"></i>
          Edit</b-button
        >
        <b-button
          variant="secondary"
          :to="{ name: 'case-copy', params: { id: data.item.id } }"
          v-if="!data.item.userHasWriteAccess"
        >
          <i class="fa fa-copy" aria-hidden="true"></i>
          Copy</b-button
        >
        <b-button
          variant="warning"
          @click="claimCase(data.item.id)"
          title="Claim ownership of this case"
          v-if="!data.item.userHasWriteAccess && data.item.userIsProjectOwner"
        >
          <i class="fa fa-hand-paper" aria-hidden="true"></i>
          Claim
        </b-button>
      </template>
      <template #row-details="row">
        <b-card
          class="my-workspaces-card"
          :title="`My ${row.item.title} Workspaces`"
          title-tag="h6"
          v-if="getWorkspacesForCase(row.item).length > 0"
        >
          <my-workspaces :workspaces="getWorkspacesForCase(row.item)" />
          <b-button
            @click="newWorkspace(row.item)"
            variant="primary"
            :title="`Create new workspace using the ${row.item.title} case`"
            :disabled="!row.item.useable"
          >
            <i class="fa fa-map" aria-hidden="true"></i>
            New Workspace</b-button
          >
        </b-card>
        <b-button
          v-else
          @click="newWorkspace(row.item)"
          variant="primary"
          :title="`Create new workspace using the ${row.item.title} case`"
          :disabled="!row.item.useable"
        >
          <i class="fa fa-map" aria-hidden="true"></i>
          Create New Workspace</b-button
        >
        <div v-if="!row.item.useable" class="small text-muted">
          Note: you cannot create a workspace with
          <strong>{{ row.item.title }}</strong> until it has at least one source
          dataset and one sink dataset.
        </div>
      </template>
    </b-table>
  </div>
</template>

<script>
import MyWorkspaces from "./MyWorkspaces.vue";
const { session, utils } = AiravataAPI;
export default {
  components: { MyWorkspaces },
  name: "cases-container",
  props: {
    projectId: {
      type: [String, Number],
      required: true,
    },
  },
  data() {
    return {
      cases: null,
      userWorkspaces: null,
    };
  },
  created() {
    this.fetchData();
  },
  methods: {
    fetchData() {
      utils.FetchUtils.get(
        `/maptool/api/cases/?project=${encodeURIComponent(this.projectId)}`
      ).then((cases) => {
        this.cases = cases;
      });
      utils.FetchUtils.get(
        `/maptool/api/workspaces/?project=${encodeURIComponent(
          this.projectId
        )}&owner=${encodeURIComponent(session.Session.username)}`
      ).then((workspaces) => {
        this.userWorkspaces = workspaces;
      });
    },
    claimCase(caseId) {
      utils.FetchUtils.post(
        `/maptool/api/cases/${caseId}/claim_ownership/`
      ).then(this.fetchData);
      // TODO: handle failure
    },
    getWorkspacesForCase(aCase) {
      if (this.userWorkspaces) {
        return this.userWorkspaces.filter((w) => w.case === aCase.id);
      } else {
        return [];
      }
    },
    newWorkspace(aCase) {
      const workspace = {
        name: `Workspace for ${aCase.title}, ${new Date().toLocaleString(
          "en-US",
          {
            dateStyle: "short",
            timeStyle: "short",
          }
        )}`,
        description: "",
        case: aCase.id,
        scenarios: [],
      };
      utils.FetchUtils.post("/maptool/api/workspaces/", workspace).then(
        (ws) => {
          window.location = `/maptool/build?workspace=${ws.id}`;
        }
      );
    },
  },
  computed: {
    caseFields() {
      return ["title", "owner", "actions"];
    },
    caseItems() {
      if (!this.cases) {
        return [];
      } else {
        return this.cases.map((aCase) => {
          return {
            id: aCase.id,
            title: aCase.title,
            description: aCase.description,
            owner: aCase.owner,
            userHasWriteAccess: aCase.userHasWriteAccess,
            userIsProjectOwner: aCase.userIsProjectOwner,
            actions: null,
            useable: aCase.useable,
            _showDetails: true,
          };
        });
      }
    },
  },
  watch: {
    projectId: "fetchData",
  },
};
</script>

<style scoped>
.my-workspaces-card {
  margin-bottom: 0px;
}
</style>
