function display_result_sample() {
    //var layercontrol = new L.control.layers();
    $.getJSON('/static/Data/result_source.geojson', function (data) {
        var result_sourceLayer = new L.geoJSON(data, {
            pointToLayer: function (feature, latlng) {
                //var mypopup = L.popup().setContent(content_str);
                var mymarker = L.circleMarker(latlng, {
                    radius: 8,
                    fillColor: "red",
                    color: "#000",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.7
                });
                //mymarker.bindPopup(mypopup);
                return mymarker;
            }
        });
        map.addLayer(result_sourceLayer);
        layercontrol.addOverlay(result_sourceLayer, "Sources");
    });
    $.getJSON('/static/Data/result_sink.geojson', function (data) {
        var result_sinkLayer = new L.geoJSON(data, {
            pointToLayer: function (feature, latlng) {
                //var mypopup = L.popup().setContent(content_str);
                var mymarker = L.circleMarker(latlng, {
                    radius: 8,
                    fillColor: "green",
                    color: "#000",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.7
                });
                //mymarker.bindPopup(mypopup);
                return mymarker;
            }
        });
        map.addLayer(result_sinkLayer);
        layercontrol.addOverlay(result_sinkLayer, "Sinks");
    });
    $.getJSON('/static/Data/SoutheastUS_Network.json', function (data) {
        var result_candidnetworkLayer = new L.geoJSON(data, {
            style: {
                color: "black",
                opacity: 0.5,
                weight: 2
            }
        });
        map.addLayer(result_candidnetworkLayer);
        layercontrol.addOverlay(result_candidnetworkLayer, "Candidate");

    });
    $.getJSON('/static/Data/result_network_110MTyr.geojson', function (data) {
        var result_110networkLayer = new L.geoJSON(data);
        map.addLayer(result_110networkLayer);
        layercontrol.addOverlay(result_110networkLayer, "110 MTyr");
    });
    $.getJSON('/static/Data/result_network_50MTyr.geojson', function (data) {
        var result_50networkLayer = new L.geoJSON(data, {
            style: {
                color: "Green"
            }
        });
        map.addLayer(result_50networkLayer);
        layercontrol.addOverlay(result_50networkLayer, "50 MTyr");
    });
    $.getJSON('/static/Data/result_network_5MTyr.geojson', function (data) {
        result_5networkLayer = new L.geoJSON(data, {
            style: {
                color: "red"
            }
        });
        map.addLayer(result_5networkLayer);
        layercontrol.addOverlay(result_5networkLayer, "5 MTyr");
    });
    layercontrol.addTo(map);

}

map = L.map('map', {
    cursor: true
}).setView([32.00, -85.43], 6);

osmUrl = '//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
osmAttrib = 'Map data © <a href="//openstreetmap.org">OpenStreetMap</a> contributors';
osm = new L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
    maxZoom: 20,
    subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
}).addTo(map);

var baseLayers = {
    "OpenStreetMap": osm
};
var layercontrol = new L.control.layers(null, null, {
    collapsed: false
});

map.createPane("polygonsPane");
map.createPane("linesPane");
map.createPane("pointsPane");

var source_all_test_layer_1 = L.tileLayer.betterWms("https://simccs.org/geoserver/SimCCS/ows?", {
    //layers: 'SimCCS_Sources_Snapper',
    layers: 'Sources_082819_SimCCS_Format',
    format: 'image/png',
    transparent: true,
    attribution: "SimCCS",
    propertyName: 'Name,Type',
    zIndex: 99
});

// var sink_sco2t_layer = L.tileLayer.wms("http://gf8.ucs.indiana.edu/geoserver/SimCCS/wms?", {
//     layers: 'SimCCS:SCO2T_SALINE_Test',
//     format: 'image/png',
//     transparent: true,
//     attribution: "SimCCS",
//     zIndex:2
// });

var sink_sco2t_layer = L.tileLayer.betterWms("https://simccs.org/geoserver/SimCCS/wms?", {
    layers: 'sco2t_national_v1_10k',
    format: 'image/png',
    transparent: true,
    attribution: "SimCCS",
    propertyName: 'name,sinkcapacity,sinkfixedcost,wellfixedcost,wellvarom',
    zIndex: 2
});

var sink_oil_eor_layer = L.tileLayer.wms("https://simccs.org/geoserver/SimCCS/wms?", {
    layers: 'SimCCS:NATCARB_OG_Test',
    format: 'image/png',
    transparent: true,
    zIndex: 3
});