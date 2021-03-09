import Vue from "vue";
import BootstrapVue from "bootstrap-vue";
import router from "./router";

// import 'bootstrap/dist/css/bootstrap.css'
import "bootstrap-vue/dist/bootstrap-vue.css";
import "./assets/styles.scss";

Vue.use(BootstrapVue);

new Vue({
  router,
  // entire base view is just the router outlet
  render: (h) => h("router-view"),
}).$mount("#projects");
