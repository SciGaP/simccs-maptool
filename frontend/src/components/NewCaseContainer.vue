<template>
  <case-editor :value="aCase" @submit="onSubmit" />
</template>

<script>
import CaseEditor from "./CaseEditor.vue";

const { utils } = AiravataAPI;
export default {
  components: { CaseEditor },
  name: "new-case-container",
  data() {
    return {
      aCase: {
        title: null,
        description: null,
        maptool: {
          bbox: null,
          data: [],
        },
      },
    };
  },
  methods: {
    onSubmit(newCase) {
      utils.FetchUtils.post("/maptool/api/cases/", newCase).then(() => {
        // TODO: add a success message
        this.$router.push({ path: "/" });
      });
    },
  },
};
</script>
