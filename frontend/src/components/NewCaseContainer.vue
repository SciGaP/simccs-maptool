<template>
  <b-card :title="cardTitle">
    <b-row>
      <b-col>
        <b-form @submit="onSubmit">
          <b-form-group label="Title">
            <b-form-input v-model="aCase.title" required></b-form-input>
          </b-form-group>
          <b-form-group label="Description">
            <b-form-input v-model="aCase.description"></b-form-input>
          </b-form-group>
          <b-card>
            <b-form-group label="Source Dataset">
              <b-form-select
                v-model="sourceDataset.dataset"
                :options="sourceDatasetOptions"
              >
                <template #first>
                  <b-form-select-option :value="null"
                    >-- Please select an option --</b-form-select-option
                  >
                </template>
              </b-form-select>
            </b-form-group>
            <b-form-group label="Style" v-if="sourceDataset.dataset">
              <b-form-input v-model="sourceDataset.style"></b-form-input>
            </b-form-group>
            <b-form-group label="Popup Fields" v-if="sourceDataset.dataset">
              <b-form-tags
                v-model="sourceDataset.popup"
                size="lg"
                add-on-change
                no-outer-focus
                class="mb-2"
              >
                <template
                  v-slot="{
                    tags,
                    inputAttrs,
                    inputHandlers,
                    disabled,
                    removeTag,
                  }"
                >
                  <ul
                    v-if="tags.length > 0"
                    class="list-inline d-inline-block mb-2"
                  >
                    <li v-for="tag in tags" :key="tag" class="list-inline-item">
                      <b-form-tag
                        @remove="removeTag(tag)"
                        :title="tag"
                        :disabled="disabled"
                        variant="info"
                        >{{ tag }}</b-form-tag
                      >
                    </li>
                  </ul>
                  <b-form-select
                    v-bind="inputAttrs"
                    v-on="inputHandlers"
                    :disabled="
                      disabled || sourceDatasetPopupFieldOptions.length === 0
                    "
                    :options="sourceDatasetPopupFieldOptions"
                  >
                    <template #first>
                      <!-- This is required to prevent bugs with Safari -->
                      <option disabled value=""
                        >Choose a popup field ...</option
                      >
                    </template>
                  </b-form-select>
                </template>
              </b-form-tags>
            </b-form-group>
          </b-card>
          <b-card>
            <b-form-group label="Sink Dataset">
              <b-form-select
                v-model="sinkDataset.dataset"
                :options="sinkDatasetOptions"
              >
                <template #first>
                  <b-form-select-option :value="null"
                    >-- Please select an option --</b-form-select-option
                  >
                </template>
              </b-form-select>
            </b-form-group>
            <b-form-group label="Style" v-if="sinkDataset.dataset">
              <b-form-input v-model="sinkDataset.style"></b-form-input>
            </b-form-group>
            <b-form-group label="Popup Fields" v-if="sinkDataset.dataset">
              <b-form-tags
                v-model="sinkDataset.popup"
                size="lg"
                add-on-change
                no-outer-focus
                class="mb-2"
              >
                <template
                  v-slot="{
                    tags,
                    inputAttrs,
                    inputHandlers,
                    disabled,
                    removeTag,
                  }"
                >
                  <ul
                    v-if="tags.length > 0"
                    class="list-inline d-inline-block mb-2"
                  >
                    <li v-for="tag in tags" :key="tag" class="list-inline-item">
                      <b-form-tag
                        @remove="removeTag(tag)"
                        :title="tag"
                        :disabled="disabled"
                        variant="info"
                        >{{ tag }}</b-form-tag
                      >
                    </li>
                  </ul>
                  <b-form-select
                    v-bind="inputAttrs"
                    v-on="inputHandlers"
                    :disabled="
                      disabled || sinkDatasetPopupFieldOptions.length === 0
                    "
                    :options="sinkDatasetPopupFieldOptions"
                  >
                    <template #first>
                      <!-- This is required to prevent bugs with Safari -->
                      <option disabled value=""
                        >Choose a popup field ...</option
                      >
                    </template>
                  </b-form-select>
                </template>
              </b-form-tags>
            </b-form-group>
          </b-card>
          <b-form-group
            label="Bounding Box"
            description="Pan/zoom the map to update the bounding box"
          >
            <b-form-input :value="bboxDisplay" readonly></b-form-input>
          </b-form-group>
          <b-button type="submit" variant="primary">Submit</b-button>
        </b-form>
      </b-col>
      <b-col>
        <div class="map" ref="map"></div>
      </b-col>
    </b-row>
  </b-card>
</template>

<script>
import "leaflet/dist/leaflet.css";
import L from "leaflet";

const { utils } = AiravataAPI;
export default {
  name: "new-case-container",
  data() {
    return {
      aCase: {
        title: null,
        description: null,
      },
      sourceDataset: {
        dataset: null, // dataset.id
        style: null,
        bbox: null,
        popup: [],
      },
      sinkDataset: {
        dataset: null, // dataset.id
        style: null,
        bbox: null,
        popup: [],
      },
      datasets: null,
      map: null,
      mapBounds: null,
    };
  },
  created() {
    utils.FetchUtils.get("/maptool/api/datasets/").then((datasets) => {
      this.datasets = datasets;
    });
  },
  mounted() {
    this.initMap();
  },
  destroyed() {
    this.destroyMap();
  },
  computed: {
    cardTitle() {
      return this.aCase.title ? this.aCase.title : "New Case";
    },
    sourceDatasets() {
      if (this.datasets) {
        return this.datasets.filter((ds) => ds.type === "source");
      } else {
        return [];
      }
    },
    sourceDatasetOptions() {
      const options = this.sourceDatasets.map((ds) => {
        return {
          text: ds.name,
          value: ds.id,
        };
      });
      return utils.StringUtils.sortIgnoreCase(options, (o) => o.text);
    },
    sourceDatasetPopupFieldOptions() {
      // TODO: pull fields from properties in the source geojson file
      const allOptions = ["Name", "CapCO2", "TotalUnitCost"];
      return allOptions.filter(
        (o) => this.sourceDataset.popup.indexOf(o) === -1
      );
    },
    sinkDatasets() {
      if (this.datasets) {
        return this.datasets.filter((ds) => ds.type === "sink");
      } else {
        return [];
      }
    },
    sinkDatasetOptions() {
      const options = this.sinkDatasets.map((ds) => {
        return {
          text: ds.name,
          value: ds.id,
        };
      });
      return utils.StringUtils.sortIgnoreCase(options, (o) => o.text);
    },
    sinkDatasetPopupFieldOptions() {
      // TODO: pull fields from properties in the sink geojson file
      const allOptions = ["Name", "StorageCap", "TotalUnitCost"];
      return allOptions.filter((o) => this.sinkDataset.popup.indexOf(o) === -1);
    },
    bboxArray() {
      if (!this.mapBounds) {
        return null;
      }
      return [
        this.mapBounds.getWest(),
        this.mapBounds.getSouth(),
        this.mapBounds.getEast(),
        this.mapBounds.getNorth(),
      ];
    },
    bboxDisplay() {
      if (!this.bboxArray) {
        return null;
      }
      return this.bboxArray.map((c) => c.toFixed(2)).join(", ");
    },
  },
  methods: {
    onSubmit(event) {
      event.preventDefault();
      const newCase = this.aCase;
      newCase.maptool = {
        bbox: this.bboxArray,
        data: [this.sourceDataset, this.sinkDataset],
      };
      utils.FetchUtils.post("/maptool/api/cases/", newCase).then(() => {
        // TODO: add a success message
        this.$router.push({ path: "/" });
      });
    },
    initMap() {
      this.map = L.map(this.$refs.map, { cursor: true }).setView(
        [32.0, -85.43],
        6
      );
      new L.tileLayer("https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", {
        maxZoom: 20,
        subdomains: ["mt0", "mt1", "mt2", "mt3"],
      }).addTo(this.map);
      this.mapBounds = this.map.getBounds();
      this.map.on("load moveend", (e) => {
        console.log(e);
        this.mapBounds = this.map.getBounds();
      });
    },
    destroyMap() {
      this.map.remove();
    },
  },
};
</script>

<style scoped>
.map {
  height: 100%;
}
</style>
