<template>
  <b-card>
    <b-nav tabs>
      <b-nav-item
        exact-active-class="active"
        exact
        :to="{
          name: 'project-cases',
          params: { projectId },
        }"
        >Cases</b-nav-item
      >
      <b-nav-item
        exact-active-class="active"
        exact
        :to="{
          name: 'project-datasets',
          params: { projectId },
        }"
        >Datasets</b-nav-item
      >
      <b-nav-item
        exact-active-class="active"
        exact
        :to="{
          name: 'project-experiments',
          params: { projectId },
        }"
        >Experiments</b-nav-item
      >
    </b-nav>
    <router-view></router-view>
  </b-card>
</template>

<script>
export default {
  props: {
    projectId: {
      type: [String, Number],
      required: true,
    },
  },
};
</script>
