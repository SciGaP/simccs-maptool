<template>
  <b-card :title="cardTitle">
    <b-row>
      <b-col>
        <b-form @submit="onSubmit">
          <b-form-group label="Title" label-class="required">
            <b-form-input
              v-model="$v.aCase.title.$model"
              :state="validateState($v.aCase.title)"
              required
            ></b-form-input>
            <b-form-invalid-feedback v-if="!$v.aCase.title.required"
              >This field is required.</b-form-invalid-feedback
            >
            <b-form-invalid-feedback v-if="!$v.aCase.title.serverValidation">{{
              this.serverValidationErrors.title.join(" ")
            }}</b-form-invalid-feedback>
          </b-form-group>
          <b-form-group label="Description">
            <b-form-input v-model="aCase.description"></b-form-input>
          </b-form-group>
          <template v-if="datasetsLoaded">
            <b-card
              v-for="datasetSelection in aCase.maptool.data"
              :key="datasetSelection.dataset"
              :title="getDatasetSelectionTitle(datasetSelection)"
              title-tag="h5"
              no-body
            >
              <b-card-body>
                <b-card-title title-tag="div">
                  <h5 class="mb-0">
                    {{ getDatasetSelectionTitle(datasetSelection) }}

                    <small
                      ><dataset-type-badge
                        v-if="getDatasetSelectionType(datasetSelection)"
                        :type="getDatasetSelectionType(datasetSelection)"
                    /></small>
                  </h5>
                </b-card-title>
                <b-form-group>
                  <b-form-select
                    :value="datasetSelection.dataset"
                    @input="onInputDatasetSelection(datasetSelection, $event)"
                  >
                    <template #first>
                      <b-form-select-option :value="null" disabled
                        >-- Please select a dataset --</b-form-select-option
                      >
                    </template>
                    <b-form-select-option-group
                      label="Sources"
                      :options="getSourceDatasetOptions(datasetSelection)"
                    >
                      <b-form-select-option :value="'create-source'"
                        >Create a new source dataset ...</b-form-select-option
                      >
                    </b-form-select-option-group>
                    <b-form-select-option-group
                      label="Sinks"
                      :options="getSinkDatasetOptions(datasetSelection)"
                    >
                      <b-form-select-option :value="'create-sink'"
                        >Create a new sink dataset ...</b-form-select-option
                      >
                    </b-form-select-option-group>
                  </b-form-select>
                </b-form-group>
                <b-form-group label="Style" v-if="datasetSelection.dataset">
                  <b-form-select
                    v-model="datasetSelection.style"
                    :options="getStyleOptions(datasetSelection.dataset)"
                  >
                    <template #first>
                      <b-form-select-option :value="null"
                        >-- Select a property to style --</b-form-select-option
                      >
                    </template>
                  </b-form-select>
                </b-form-group>
                <b-form-group label="Symbol" v-if="datasetSelection.dataset">
                  <b-form-select
                    v-model="datasetSelection.symbol"
                    :options="symbolOptions"
                    @change="updateSymbol(datasetSelection)"
                  >
                  </b-form-select>
                </b-form-group>
                <b-form-group
                  label="Popup Fields"
                  v-if="datasetSelection.dataset"
                >
                  <b-form-tags
                    v-model="datasetSelection.popup"
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
                        <li
                          v-for="tag in tags"
                          :key="tag"
                          class="list-inline-item"
                        >
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
                          disabled ||
                          datasetPopupFieldOptions(datasetSelection).length ===
                            0
                        "
                        :options="datasetPopupFieldOptions(datasetSelection)"
                      >
                        <template #first>
                          <!-- This is required to prevent bugs with Safari -->
                          <option disabled value="">
                            Choose a popup field ...
                          </option>
                        </template>
                      </b-form-select>
                    </template>
                  </b-form-tags>
                </b-form-group>
              </b-card-body>
              <template #footer>
                <b-button
                  variant="secondary"
                  @click="removeDataset(datasetSelection)"
                >
                  Remove
                </b-button>
              </template>
            </b-card>
          </template>
          <b-button
            variant="secondary"
            @click="addDataset"
            :disabled="!addDatasetEnabled"
            >Add Dataset</b-button
          >
          <new-dataset-modal
            ref="newDatasetModal"
            :datasetType="newDatasetType"
            :projectId="projectId"
            @created="newDatasetCreated"
          />
          <div>
            <b-button
              type="submit"
              variant="primary"
              class="mt-4"
              :disabled="$v.$invalid"
              >Save</b-button
            >
          </div>
        </b-form>
      </b-col>
      <b-col cols="8">
        <div class="map-container">
          <div class="map" ref="map"></div>
        </div>
        <b-form-group
          label="Bounding Box"
          description="Pan/zoom the map to update the bounding box"
        >
          <b-form-input :value="bboxDisplay" readonly></b-form-input>
        </b-form-group>
      </b-col>
    </b-row>
  </b-card>
</template>

<script>
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import "leaflet-svg-shape-markers";
import { validationMixin } from "vuelidate";
import { required } from "vuelidate/lib/validators";
import validateFromServer from "../validators/validateFromServer";
import { validateState } from "../validators/formHelpers";
import NewDatasetModal from "./NewDatasetModal.vue";
import DatasetTypeBadge from "./DatasetTypeBadge.vue";

const { utils } = AiravataAPI;
export default {
  components: { NewDatasetModal, DatasetTypeBadge },
  mixins: [validationMixin],
  name: "case-editor",
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
  },
  data() {
    return {
      aCase: JSON.parse(JSON.stringify(this.value)), // clone the input
      datasets: null,
      map: null,
      layercontrol: null,
      layers: {},
      mapBounds: null,
      submittedData: null,
      geojson: {},
      newDatasetType: null,
    };
  },
  validations() {
    return {
      aCase: {
        title: {
          required,
          serverValidation: validateFromServer(
            () => (this.submittedData ? this.submittedData.title : null),
            () =>
              this.serverValidationErrors
                ? this.serverValidationErrors.title
                : null
          ),
        },
        maptool: {
          data: {
            $each: {
              dataset: {
                required,
              },
            },
          },
        },
      },
    };
  },
  created() {
    // TODO: pass in datasets?
    utils.FetchUtils.get(
      `/maptool/api/datasets/?project=${this.projectId}`
    ).then((datasets) => {
      this.datasets = datasets;
    });
  },
  mounted() {
    this.initMap();
    if (this.aCase.datasets) {
      for (const ds of this.aCase.datasets) {
        this.loadDatasetLayer(ds);
      }
    }
  },
  destroyed() {
    this.destroyMap();
  },
  computed: {
    projectId() {
      return this.aCase.simccs_project;
    },
    cardTitle() {
      return this.aCase.title ? this.aCase.title : "New Case";
    },
    datasetsLoaded() {
      return this.datasets !== null;
    },
    sourceDatasets() {
      if (this.datasets) {
        const sources = this.datasets.filter((ds) => ds.type === "source");
        // Add deleted sources that are used by the case to the list
        if (this.aCase.datasets) {
          this.aCase.datasets
            .filter((ds) => ds.type === "source" && ds.deleted)
            .forEach((ds) => {
              sources.push(ds);
            });
        }
        return sources;
      } else {
        return [];
      }
    },
    sinkDatasets() {
      if (this.datasets) {
        const sinks = this.datasets.filter((ds) => ds.type === "sink");
        // Add deleted sinks that are used by the case to the list
        if (this.aCase.datasets) {
          this.aCase.datasets
            .filter((ds) => ds.type === "sink" && ds.deleted)
            .forEach((ds) => {
              sinks.push(ds);
            });
        }
        return sinks;
      } else {
        return [];
      }
    },
    addDatasetEnabled() {
      return !this.aCase.maptool.data.find((d) => d.dataset === null);
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
    symbolOptions() {
      return [
        "diamond",
        "square",
        "triangle-up",
        "triangle-down",
        "arrowhead-up",
        "arrowhead-down",
        "circle",
        //"x",
      ];
    },
  },
  methods: {
    onSubmit(event) {
      event.preventDefault();
      const newCase = this.aCase;
      newCase.maptool.bbox = this.bboxArray;
      this.submittedData = JSON.parse(JSON.stringify(newCase)); // deep clone
      this.$emit("submit", newCase);
    },
    initMap() {
      this.map = L.map(this.$refs.map, { cursor: true });
      if (this.aCase.maptool.bbox) {
        const [west, south, east, north] = this.aCase.maptool.bbox;
        this.map.fitBounds([
          [south, west],
          [north, east],
        ]);
      } else {
        this.map.setView([32.0, -85.43], 6);
      }
      new L.tileLayer("https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", {
        maxZoom: 20,
        subdomains: ["mt0", "mt1", "mt2", "mt3"],
      }).addTo(this.map);
      this.layercontrol = L.control
        .layers(null, null, { collapsed: false })
        .addTo(this.map);
      this.mapBounds = this.map.getBounds();
      this.map.on("load moveend", () => {
        this.mapBounds = this.map.getBounds();
      });
    },
    destroyMap() {
      this.map.remove();
    },
    getSourceDatasetOptions(datasetSelection) {
      const notAlreadySelected = (ds) => {
        const alreadySelected = this.aCase.maptool.data.find(
          (d) => d.dataset === ds.id
        );
        return !alreadySelected || alreadySelected === datasetSelection;
      };
      const sourceOptions = this.sourceDatasets.map((ds) => {
        return {
          text: `${ds.name}${ds.deleted ? " (deleted)" : ""}`,
          value: ds.id,
          // NOTE: disable, don't filter, already selected options.
          // Dynamically removing options messes up the selected one.
          disabled: !notAlreadySelected(ds) || ds.deleted,
        };
      });
      utils.StringUtils.sortIgnoreCase(sourceOptions, (o) => o.text);
      return sourceOptions;
    },
    getSinkDatasetOptions(datasetSelection) {
      const notAlreadySelected = (ds) => {
        const alreadySelected = this.aCase.maptool.data.find(
          (d) => d.dataset === ds.id
        );
        return !alreadySelected || alreadySelected === datasetSelection;
      };
      const sinkOptions = this.sinkDatasets.map((ds) => {
        return {
          text: `${ds.name}${ds.deleted ? " (deleted)" : ""}`,
          value: ds.id,
          disabled: !notAlreadySelected(ds) || ds.deleted,
        };
      });
      utils.StringUtils.sortIgnoreCase(sinkOptions, (o) => o.text);
      return sinkOptions;
    },
    datasetPopupFieldOptions(datasetSelection) {
      if (!this.datasets || !datasetSelection.dataset) {
        return [];
      }
      const props = this.getGeojsonProperties(
        this.geojson[datasetSelection.dataset]
      );
      props.sort();
      return props.filter((o) => datasetSelection.popup.indexOf(o) === -1);
    },
    addDataset() {
      this.aCase.maptool.data.push({
        dataset: null,
        style: null,
        bbox: null,
        popup: [],
        symbol: "circle",
      });
    },
    removeDataset(datasetSelection) {
      const i = this.aCase.maptool.data.indexOf(datasetSelection);
      this.aCase.maptool.data.splice(i, 1);
    },
    validateState,
    addDatasetLayer(dataset, geojson) {
      const fillColor = this.getDatasetLayerColor(dataset);
      const shape = this.getDatasetLayerShape(dataset);
      const layer = new L.geoJSON(geojson, {
        pointToLayer: function (feature, latlng) {
          const marker = L.shapeMarker(latlng, {
            shape: shape,
            radius: 8,
            fillColor: fillColor,
            color: "#000",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8,
          });
          return marker;
        },
        onEachFeature: (feature, layer) => {
          layer.bindTooltip(() => {
            return this.getPopupTooltip(dataset, feature);
          });
        },
      });
      this.layercontrol.addOverlay(layer, dataset.name);
      layer.addTo(this.map);
      this.$set(this.layers, dataset.id, layer);
    },
    getPopupTooltip(dataset, feature) {
      const data = this.aCase.maptool.data.find(
        (d) => d.dataset === dataset.id
      );
      const popupFields = data.popup;
      const title =
        dataset.type === "source"
          ? "Source"
          : dataset.type === "sink"
          ? "Sink"
          : null;
      let tooltip = `<strong>${title}<br>`;
      for (const field of popupFields) {
        tooltip += `${field}: ${feature.properties[field]}<br>`;
      }
      tooltip += "</strong>";
      return tooltip;
    },
    getDatasetLayerColor(dataset) {
      return dataset.type === "source" ? "red" : "green";
    },
    getDatasetLayerShape(dataset) {
      const data = this.aCase.maptool.data.find(
        (d) => d.dataset === dataset.id
      );
      return data.symbol;
    },
    removeDatasetLayer(datasetId) {
      const layer = this.layers[datasetId];
      this.layercontrol.removeLayer(layer);
      layer.remove();
      this.$delete(this.layers, datasetId);
    },
    updateSymbol(datasetSelection) {
      const datasetId = datasetSelection.dataset;
      const layer = this.layers[datasetId];
      layer.eachLayer(function (layer) {
        layer.setStyle({ shape: datasetSelection.symbol });
      });
    },
    getDataset(datasetId) {
      // sourceDatasets and sinkDatasets include also a Case's deleted datasets
      return this.sourceDatasets
        .concat(this.sinkDatasets)
        .find((ds) => ds.id === datasetId);
    },
    loadDatasetLayer(dataset) {
      return utils.FetchUtils.get(dataset.url).then((geojson) => {
        this.$set(this.geojson, dataset.id, geojson);
        this.addDatasetLayer(dataset, geojson);
      });
    },
    getGeojsonProperties(geojson) {
      if (geojson && geojson.features && geojson.features.length > 0) {
        return Object.keys(geojson.features[0].properties);
      } else {
        return [];
      }
    },
    getStyleOptions(datasetId) {
      const props = this.getGeojsonProperties(this.geojson[datasetId]);
      props.sort();
      return props;
    },
    getDatasetSelectionTitle(datasetSelection) {
      const datasetId = datasetSelection.dataset;
      if (datasetId) {
        const dataset = this.getDataset(datasetId);
        if (dataset) {
          return dataset.name;
        } else {
          return null;
        }
      } else {
        return null;
      }
    },
    getDatasetSelectionType(datasetSelection) {
      const datasetId = datasetSelection.dataset;
      if (datasetId) {
        const dataset = this.getDataset(datasetId);
        if (dataset) {
          return dataset.type;
        } else {
          return null;
        }
      } else {
        return null;
      }
    },
    createDataset(datasetType) {
      this.newDatasetType = datasetType;
      this.$refs["newDatasetModal"].show();
    },
    newDatasetCreated(dataset) {
      this.datasets.push(dataset);
      // If there is a null datasetSelection, remove it
      const nullIndex = this.aCase.maptool.data.findIndex(
        (d) => d.dataset === null
      );
      if (nullIndex) {
        this.aCase.maptool.data.splice(nullIndex, 1);
      }
      this.aCase.maptool.data.push({
        dataset: dataset.id,
        style: null,
        bbox: null,
        popup: [],
      });
    },
    onInputDatasetSelection(datasetSelection, value) {
      // 'create-source' and 'create-sink' are special values for triggering
      // display of the NewDatasetModal
      if (value === "create-source") {
        this.createDataset("source");
      } else if (value === "create-sink") {
        this.createDataset("sink");
      } else {
        datasetSelection.dataset = value;
      }
    },
  },
  watch: {
    "aCase.maptool.data": {
      handler: function (data) {
        const datasetIds = data
          .map((d) => d.dataset)
          .filter((id) => id !== null);
        // Add missing datasets layers
        for (const datasetId of datasetIds) {
          if (!(datasetId in this.layers)) {
            if (!(datasetId in this.geojson)) {
              this.loadDatasetLayer(this.getDataset(datasetId));
            } else {
              const geojson = this.geojson[datasetId];
              this.addDatasetLayer(this.getDataset(datasetId), geojson);
            }
          }
        }
        // Remove layers for datasets that have been removed
        for (const datasetId of Object.keys(this.layers)) {
          if (!datasetIds.includes(parseInt(datasetId))) {
            this.removeDatasetLayer(datasetId);
          }
        }
      },
      deep: true,
    },
  },
};
</script>

<style scoped>
.map-container {
  width: 100%;
  /* set height to 3/4 of width: see https://stackoverflow.com/a/20157916 */
  padding-top: 75%;
  position: relative;
}
.map {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
</style>
