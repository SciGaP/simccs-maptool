import Vue from "vue";
import VueRouter from "vue-router";
import CasesContainer from "../components/CasesContainer.vue";
import CopyCaseContainer from "../components/CopyCaseContainer.vue";
import EditCaseContainer from "../components/EditCaseContainer.vue";
import EditDatasetContainer from "../components/EditDatasetContainer.vue";
import EditProjectContainer from "../components/EditProjectContainer.vue";
import NewDatasetContainer from "../components/NewDatasetContainer.vue";
import NewCaseContainer from "../components/NewCaseContainer.vue";
import NewProjectContainer from "../components/NewProjectContainer.vue";
import ProjectsHomeContainer from "../components/ProjectsHomeContainer.vue";
import ProjectContainer from "../components/ProjectContainer.vue";
import ViewDatasetContainer from "../components/ViewDatasetContainer.vue";

Vue.use(VueRouter);

const routes = [
  {
    path: "/projects",
    component: ProjectsHomeContainer,
  },
  {
    path: "/projects/new",
    component: NewProjectContainer,
  },
  {
    path: "/projects/:projectId/edit",
    component: EditProjectContainer,
    props: true,
  },
  {
    path: "/projects/:projectId",
    component: ProjectContainer,
    props: true,
    children: [
      { path: "datasets/new", component: NewDatasetContainer },
      {
        path: "datasets/:id/edit",
        component: EditDatasetContainer,
        props: true,
        name: "dataset",
      },
      {
        path: "datasets/:id",
        component: ViewDatasetContainer,
        props: true,
        name: "dataset-view",
      },
      { path: "cases/new", component: NewCaseContainer },
      { path: "", component: CasesContainer, name: "project" },
      {
        path: "cases/:id/copy",
        component: CopyCaseContainer,
        props: true,
        name: "case-copy",
      },
      {
        path: "cases/:id",
        component: EditCaseContainer,
        props: true,
        name: "case",
      },
    ],
  },
];

const router = new VueRouter({
  mode: "history",
  base: "/maptool/build",
  routes,
});

export default router;
