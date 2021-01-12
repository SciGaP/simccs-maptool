import Vue from "vue";
import VueRouter from "vue-router";
import CasesContainer from "../components/CasesContainer.vue";
import EditCaseContainer from "../components/EditCaseContainer.vue";
import NewDatasetContainer from "../components/NewDatasetContainer.vue";
import NewCaseContainer from "../components/NewCaseContainer.vue";

Vue.use(VueRouter);

const routes = [
  { path: "/", component: CasesContainer },
  { path: "/datasets/new", component: NewDatasetContainer },
  { path: "/cases/new", component: NewCaseContainer },
  {
    path: "/cases/:id",
    component: EditCaseContainer,
    props: true,
    name: "case",
  },
];

const router = new VueRouter({
  mode: "history",
  base: "/maptool/cases/",
  routes,
});

export default router;
