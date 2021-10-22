L.CursorHandler = L.Handler.extend({

    addHooks: function () {
        this._popup = new L.Popup();
        this._map.on('mouseover', this._open, this);
        this._map.on('mousemove', this._update, this);
        this._map.on('mouseout', this._close, this);
    },

    removeHooks: function () {
        this._map.off('mouseover', this._open, this);
        this._map.off('mousemove', this._update, this);
        this._map.off('mouseout', this._close, this);
    },

    _open: function (e) {
        this._update(e);
        this._popup.openOn(this._map);
    },

    _close: function () {
        this._map.closePopup(this._popup);
    },

    _update: function (e) {
        this._popup.setLatLng(e.latlng)
            .setContent(e.latlng.toString());
    }


});

function display_result_sample(){
    //var layercontrol = new L.control.layers();
    $.getJSON('/static/Data/result_source.geojson',function (data) {
        var result_sourceLayer = new L.geoJSON(data, {
            pointToLayer: function (feature, latlng) {
                //var mypopup = L.popup().setContent(content_str);
                var mymarker = L.circleMarker(latlng,{radius: 8,fillColor: "red",
                color: "#000",weight: 1,opacity: 1,fillOpacity: 0.7});
                //mymarker.bindPopup(mypopup);
                return mymarker;       
            }
        });
        map.addLayer(result_sourceLayer);
        layercontrol.addOverlay(result_sourceLayer,"Sources");
    });
    $.getJSON('/static/Data/result_sink.geojson',function (data) {
        var result_sinkLayer = new L.geoJSON(data, {
            pointToLayer: function (feature, latlng) {
                //var mypopup = L.popup().setContent(content_str);
                var mymarker = L.circleMarker(latlng,{radius: 8,fillColor: "green",
                    color: "#000",weight: 1,opacity: 1,fillOpacity: 0.7});
                //mymarker.bindPopup(mypopup);
                return mymarker;       
            }
        });
        map.addLayer(result_sinkLayer);
        layercontrol.addOverlay(result_sinkLayer,"Sinks");
    });
    $.getJSON('/static/Data/SoutheastUS_Network.json',function (data) {
        var result_candidnetworkLayer = new L.geoJSON(data,{style:{color:"black",opacity:0.5,weight:2}});
        map.addLayer(result_candidnetworkLayer);
        layercontrol.addOverlay(result_candidnetworkLayer,"Candidate");

    });
    $.getJSON('/static/Data/result_network_110MTyr.geojson',function (data) {
        var result_110networkLayer = new L.geoJSON(data);
        map.addLayer(result_110networkLayer);
        layercontrol.addOverlay(result_110networkLayer,"110 MTyr");
    });
    $.getJSON('/static/Data/result_network_50MTyr.geojson',function (data) {
        var result_50networkLayer = new L.geoJSON(data,{style:{color:"Green"}});
        map.addLayer(result_50networkLayer);
        layercontrol.addOverlay(result_50networkLayer,"50 MTyr");
    });
    $.getJSON('/static/Data/result_network_5MTyr.geojson',function (data) {
        result_5networkLayer = new L.geoJSON(data,{style:{color:"red"}});
        map.addLayer(result_5networkLayer);
        layercontrol.addOverlay(result_5networkLayer,"5 MTyr");
    });
    layercontrol.addTo(map);

}

// L.Map.addInitHook('addHandler', 'cursor', L.CursorHandler);

map = L.map('map',{cursor:true}).setView([32.00,-85.43], 6);
// map=L.map('leaflet',{
//     center:[38.420836729,-87.762496593],
//     zoom:7,
//     cursor:true
// });

    osmUrl='//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    osmAttrib='Map data © <a href="//openstreetmap.org">OpenStreetMap</a> contributors';
    //osm = new L.TileLayer(osmUrl, {minZoom: 1, maxZoom: 15, attribution: osmAttrib});
    //map.addLayer(osm);
    // L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
	// attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
	// maxZoom: 18,
	// id: 'mapbox.streets',
	// accessToken: 'pk.eyJ1Ijoid2FuZzIwOCIsImEiOiJjazBkd3g4cDQwMDNpM2NtZmsxMGY2bnY2In0.n8zYH_42X598kQxtl03-iA'
    // }).addTo(map);
    //google streets
    osm = new L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',{
        maxZoom: 20,
        subdomains:['mt0','mt1','mt2','mt3']
    }).addTo(map);
    
    var baseLayers = {
        "OpenStreetMap": osm
    };
    var layercontrol = new L.control.layers(null,null,{collapsed:false});
    
    map.createPane("polygonsPane");
    map.createPane("linesPane");
    map.createPane("pointsPane");
    
    //minor change for testing
    //display_result_sample();

    //Draw the cost area of 80km
    var boundry_circle_options={

        fillColor:"#229954",
        fillOpacity:0.6,
        color:"#229954"
    };
    // L.circle([ 38.3689,-87.7659 ],80000,boundry_circle_options).addTo(map)
    bound_layer=L.circle([ 38.3689,-87.7659 ],80000,boundry_circle_options);



    // L.geoJson(path).addTo(map);

    // console.log(source_sink.length);
    // L.geoJson(source_sink).addTo(map);
    // source_sink_layer=L.geoJson(source_sonk,{
    //     pointToLayer:function(feature,latlng){
    //         return L.circleMarker(latlng,geojsonMarkerOptions).bindPopup('Source Sink');;
    //     }
    // });

//define a layercontrol layer;


// uncessary code
// var chemicalIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/co2_red_icon.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });


    // var chemicalClusters=L.markerClusterGroup();
    // $.getJSON('/static/Data/Source_Chemicals.json',function (data) {


    //     for(var i=0;i<data.length;i++){
    //         var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
    //             '<br/><b>Place</b>:'+data[i].properties.City+
    //             '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
    //           '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



    //         var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:chemicalIcon}).bindPopup(popup);
    //         chemicalClusters.addLayer(m);

    //     }

    // });
//     var coalIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/coal.jpeg',
//     iconSize:     [20, 20], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });

//     var coalClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Coal-based_Liquid_Fuel_Supply.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:coalIcon}).bindPopup(popup);
//             coalClusters.addLayer(m);

//         }

//     });
// var GHGIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/GHG.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });


//     var flourinatedClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Import_and_Export_of_Equipment_Containing_Fluorintaed_GHGs.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:GHGIcon}).bindPopup(popup);
//             flourinatedClusters.addLayer(m);

//         }

//     });
//     var industryGasIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/industry_gas.jpeg',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });


//     var industrialGasClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Industrial_Gas_Suppliers.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:industryGasIcon}).bindPopup(popup);
//             industrialGasClusters.addLayer(m);

//         }

//     });

// var co2InjectionIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/co2_injection.jpg',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });
//     var co2InjectionClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Injection_of_CO2.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:co2InjectionIcon}).bindPopup(popup);
//             co2InjectionClusters.addLayer(m);

//         }

//     });

//     var metalIcon = L.icon({

//         iconUrl:'/static/images/metal.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });
//     var metalClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Metals.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:metalIcon}).bindPopup(popup);
//             metalClusters.addLayer(m);

//         }

//     });

//     var mineralIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/mineral.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });
//     var mineralClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Minerals.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:mineralIcon}).bindPopup(popup);
//             mineralClusters.addLayer(m);

//         }

//     });

//     var naturalGasIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/natural_gas.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });
//     var naturalGasClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Natural_Gas_and_Natural_Gas_Liquids_Suppliers.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:naturalGasIcon}).bindPopup(popup);
//             naturalGasClusters.addLayer(m);

//         }

//     });


//     var otherClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Other.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]]).bindPopup(popup);
//             otherClusters.addLayer(m);

//         }

//     });
//     var petrolIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/petroleum_icon.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });

//     var petroleumClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Petroleum_Product_Suppliers.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:petrolIcon}).bindPopup(popup);
//             petroleumClusters.addLayer(m);

//         }

//     });
//     var petrolGasIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/petrol_natural_gas.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });

//     var petroleumNaturalGasClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Petroleum_and_Natural_Gas_Systems.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:petrolGasIcon}).bindPopup(popup);
//             petroleumNaturalGasClusters.addLayer(m);

//         }

//     });

//     var powerPlantIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/power_plant.png',
//     //iconSize:     [38, 35], // size of the icon
//     iconSize:     [30, 26], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });

//     var powerPlantClusters=L.markerClusterGroup({ disableClusteringAtZoom: 7 });
//     $.getJSON('/static/Data/Source_Power_Plants.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<h3>Source</h3>'+'<b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;

//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:powerPlantIcon}).bindPopup(popup);
//             powerPlantClusters.addLayer(m);

//         }

//     });

//     var pulpIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/pulp.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });
//     var pulpClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Pulp_and_Paper.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:pulpIcon}).bindPopup(popup);
//             pulpClusters.addLayer(m);

//         }

//     });

//     var refineryIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/refinery.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });

//     var refineriesClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Refineries.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:refineryIcon}).bindPopup(popup);
//             refineriesClusters.addLayer(m);

//         }

//     });

//     var co2SupplyIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/co2_suppliers.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });
//     var co2SupplyClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Pulp_and_Paper.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:co2SupplyIcon}).bindPopup(popup);
//             co2SupplyClusters.addLayer(m);

//         }

//     });

//     var wasteIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/waste.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });

//     var wasteClusters=L.markerClusterGroup();
//     $.getJSON('/static/Data/Source_Refineries.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+'<br><b>Facility</b>:'+data[i].properties.Facility_N+
//                 '<br/><b>Place</b>:'+data[i].properties.City+
//                 '<br/><b>IndustryType</b> :' + data[i].properties.Industry_T +
//               '<br/><b>Co2 Emission</b> :' + data[i].properties.CO2_Emissi;



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon:wasteIcon}).bindPopup(popup);
//             wasteClusters.addLayer(m);

//         }

//     });

//     var greenIcon = L.icon({
//     // iconUrl: 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png',
//     // iconUrl:'http://goo.gl/images/Dp5YLA',
//         iconUrl:'/static/images/co2_image.png',
//     iconSize:     [38, 35], // size of the icon
//     iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
// });
//     var ordos_source_cluster=L.markerClusterGroup();
//     $.getJSON('/static/Data/Ordos_Basin_Source.json',function (data) {


//         for(var i=0;i<data.length;i++){
//             var popup='Source Nos# '+(i+1);



//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]]).bindPopup(popup);
//             ordos_source_cluster.addLayer(m);

//         }

//     });

//     var france_source_cluster=L.markerClusterGroup();
//     $.getJSON('/static/Data/France_Source.json',function (data) {
//        for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Source</h2>'+
//                 '<br><b>Facility</b>: '+data[i].properties.NAME_GUILL+
//                 '<br/><b>Place</b>: '+data[i].properties.LOCATION_G+','+data[i].properties.SECTOR_GUI+
//               '<br/><b>Co2 Storage</b>: ' + data[i].properties.Ave_Mt+' MT';
//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]]).bindPopup(popup);
//             france_source_cluster.addLayer(m);
//        }
//     });




//     var france_sink_cluster=L.markerClusterGroup();
//         $.getJSON('/static/Data/France_Sink.json',function (data) {
//             for(var i=0;i<data.length;i++){
//             var popup='<br><h2>Sink</h2>'+'<br><b>Name:</b>: '+data[i].properties.NAME+
//                 '<br/><b>Depth</b>: '+data[i].properties.Depth+
//               '<br/><b>Capacity</b>: ' + data[i].properties.Capacity__;
//             var m=L.marker([data[i].geometry.coordinates[1],data[i].geometry.coordinates[0]],{icon: greenIcon}).bindPopup(popup);
//             france_sink_cluster.addLayer(m);
//        }



//     });
//         // map.addLayer(france_sink_cluster);
// var geojsonLineOptions = {

//                 color: 'black',
//                 weight: 2,
//                 opacity: .7,
//                 //dashArray: '20,15',
//                 //lineJoin: 'round'
//     };
//         var ut_candidate_network;
//         $.getJSON('/static/Data/UT_Network.json',function (data) {


//             ut_candidate_network=L.geoJson(data,geojsonLineOptions);



//     });
//         var albert_candidate_network;
//         $.getJSON('/static/Data/Alberta_BaseNetwork.json',function (data) {


//             albert_candidate_network=L.geoJson(data,geojsonLineOptions);



//     });
//         var illinios_candidate_network;
//         $.getJSON('/static/Data/Illinois_BaseNetwork.json',function (data) {


//             illinios_candidate_network=L.geoJson(data,geojsonLineOptions);



//     });

//         var ordos_candidate_network;
//         $.getJSON('/static/Data/Ordos_Basin_Network.json',function (data) {


//             ordos_candidate_network=L.geoJson(data,geojsonLineOptions);



//     });

//         var se_candidate_network;
//         $.getJSON('/static/Data/SoutheastUS_Network.json',function (data) {


//             se_candidate_network=L.geoJson(data,geojsonLineOptions);



//     });
//          var ne_cadidate_network;
//         $.getJSON('/static/Data/NE_Network.json',function (data) {


//             ne_candidate_network=L.geoJson(data,geojsonLineOptions);


//     });

        // var sink_coal_layer = L.tileLayer.wms("http://gf8.ucs.indiana.edu/geoserver/SimCCS/wms?", {
        //         layers: 'SimCCS:NATCARB_Coal',
        //         format: 'image/png',
        //         transparent: true
        // });

        // var sink_oil_layer=L.tileLayer.wms("http://gf8.ucs.indiana.edu/geoserver/SimCCS/wms?", {
        //         layers: 'SimCCS:NATCARB_OG',
        //         format: 'image/png',
        //         transparent: true
        // });

        // var sink_saline_layer=L.tileLayer.wms("http://gf8.ucs.indiana.edu/geoserver/SimCCS/wms?", {
        //         layers: 'SimCCS:NATCARB_SALINE',
        //         //layers: 'SimCCS:SCO2T_Database_v1_1_Cheapest_Grid',
        //         format: 'image/png',
        //         transparent: true
        // });

        // var sink_ordos_layer=L.tileLayer.wms("http://gf8.ucs.indiana.edu/geoserver/SimCCS/wms?", {
        //         layers: 'SimCCS:China_OG',
        //         format: 'image/png',
        //         transparent: true
        // });

        // var cost_surface_layer = L.tileLayer.wms("http://gf8.ucs.indiana.edu/geoserver/SimCCS/wms?", {
        //     layers: 'SimCCS:cost',
        //     format: 'image/png',
        //     transparent: true,
        //     attribution: "SimCCS",
        //     zIndex:1
        // });

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
            zIndex:2
        });

        var sink_oil_eor_layer=L.tileLayer.wms("https://simccs.org/geoserver/SimCCS/wms?", {
            layers: 'SimCCS:NATCARB_OG_Test',
            format: 'image/png',
            transparent: true,
            zIndex: 3
    });

L.Control.SolutionSummary = L.Control.extend({
    summaries: new Map(),
    el: null,

    onAdd(map) {
        const card = this.el = document.createElement('div');
        card.classList.add("card");
        const cardHeader = document.createElement('div');
        cardHeader.classList.add('card-header');
        cardHeader.textContent = "Solution Summary";
        card.appendChild(cardHeader);
        const cardBody = document.createElement('div');
        cardBody.classList.add("card-body");
        card.appendChild(cardBody);
        return card;
    },

    onRemove(map) {
        // Nothing to do here
    },

    addSolutionSummary(solutionLabel, solutionSummary) {
        this.summaries.set(solutionLabel, solutionSummary);
        this.render();
    },

    removeSolutionSummary(solutionLabel) {
        this.summaries.delete(solutionLabel);
        this.render();
    },

    render() {
        const cardBody = this.el.querySelector('.card-body');
        this.generateTable(cardBody);
    },

    generateTable(container) {
        const labels = [...this.summaries.keys()];
        const summaries = [...this.summaries.values()];
        container.innerHTML = `
            <table class="table table-sm">
                <tbody>
                <tr class="table-secondary">
                        <th scope="row">Experiment</th>
                        ${labels.map(k => `<td>${k}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Sources</th>
                        ${summaries.map(s => s.numOpenedSources).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Sinks</th>
                        ${summaries.map(s => s.numOpenedSinks).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">CO<sub>2</sub> Stored</th>
                        ${summaries.map(s => s.targetCaptureAmount.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Edges</th>
                        ${summaries.map(s => s.numEdgesOpened).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Project Length</th>
                        ${summaries.map(s => s.projectLength).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr class="table-secondary">
                        <th scope="row">Total Cost ($m/yr)</th>
                        ${labels.map(k => `<td></td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Capture</th>
                        ${summaries.map(s => s.totalCaptureCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Transport</th>
                        ${summaries.map(s => s.totalTransportCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Storage</th>
                        ${summaries.map(s => s.totalStorageCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Total</th>
                        ${summaries.map(s => s.totalCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr class="table-secondary">
                        <th scope="row">Unit Cost ($/tCO<sub>2</sub>)</th>
                        ${labels.map(k => `<td></td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Capture</th>
                        ${summaries.map(s => s.unitCaptureCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Transport</th>
                        ${summaries.map(s => s.unitTransportCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Storage</th>
                        ${summaries.map(s => s.unitStorageCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                <tr>
                        <th scope="row">Total</th>
                        ${summaries.map(s => s.unitTotalCost.toFixed(2)).map(v => `<td>${v}</td>`).join("")}
                </tr>
                </tbody>
            </table>
        `;
    }

});

L.control.solutionSummary = function(opts) {
    return new L.Control.SolutionSummary(opts);
}
