//load deafult map
map = L.map('map',{cursor:true}).setView([32.00,-85.43], 6);

//google streets
osm = new L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',{
    maxZoom: 20,
    subdomains:['mt0','mt1','mt2','mt3']
}).addTo(map);

var baseLayers = {
    "Google Street": osm
};

//create panes
map.createPane("polygonsPane");
map.createPane("linesPane");
// for sinks
map.createPane("pointsPane");
// for sources
map.createPane("toppointsPane");
// for drawing
map.createPane("drawingPane");

 // create the sidebar instance and add it to the map
 var sidebar = L.control.sidebar({ autopan: true, container: 'sidebar' }).addTo(map);
 
// default point option (source)
var sourceRadius = 9;
var sinkRadius = 7;
var geojsonMarkerOptions = {
    radius: sourceRadius,
    fillColor: "blue",
    color: "darkgrey",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.8,
    pane: "pointsPane"
};
var source_shapeMakerOptions = {
    radius: sourceRadius,
    shape: "arrowhead",
    fillColor: "blue",
    fillOpacity: 0.6,
    color: "grey",
    weight:1,
    pane: "toppointsPane"
};

var sink_shapeMakerOptions = {
    radius: sinkRadius,
    shape: "square",
    fillColor: "blue",
    fillOpacity: 0.6,
    color: "grey",
    weight:1,
    pane: "pointsPane"
};

// sink point option
var sinkMarkerOptions = {
    radius: sinkRadius,
    fillColor: "blue",
    color: "grey",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.8,
    pane: "polygonsPane"
};


// function getcolor
function getColor(d) {
    return d > 10.0 ? '#f50000' :
            d > 5.0  ? '#fdff00' :
            d > 0.0  ? '#00f905' :
                        '#FFEDA0';
}

// create a legend for coloring field
function createLegend(fieldname,symbol)
{
    //var div = L.DomUtil.create('div', 'info legend'),
    var div = L.DomUtil.create('div'),
    grades = [0, 5, 10],
    labels = [],
    from, to;
    var symbolsvg;
    console.log(symbol);
    switch(symbol) {
        case 'square':
            symbolsvg='<svg width="19" height="19"><rect width="19" height="19" style="fill:#3388ff;stroke:black;stroke-width:3;fill-opacity:0.6;stroke-opacity:1" /></svg>';
            break;
        case 'triangle-up':
            symbolsvg='<svg width="20" height="20"><polygon points="0,20 10,0 20,20" style="fill:#3388ff;stroke:black;stroke-width:2;fill-opacity:0.6;stroke-opacity:1" /></svg>';
            break;
        case 'triangle-down':
            symbolsvg='<svg width="20" height="20"><polygon points="0,0 20,0 10,20" style="fill:#3388ff;stroke:black;stroke-width:2;fill-opacity:0.6;stroke-opacity:1" /></svg>';
            break;
        case 'diamond':
            symbolsvg='<svg width="20" height="20"><polygon points="10,0 0,10 10,20 20,10" style="fill:#3388ff;stroke:black;stroke-width:2;fill-opacity:0.6;stroke-opacity:1" /></svg>';
            break;
        case 'arrowhead-down':
            symbolsvg='<svg width="20" height="20"><polygon points="0,0 10,5 20,0 10,20" style="fill:#3388ff;stroke:black;stroke-width:2;fill-opacity:0.6;stroke-opacity:1" /></svg>';
            break;
        case 'arrowhead-up':
            symbolsvg='<svg width="20" height="20"><polygon points="0,20 10,0 20,20 10,15" style="fill:#3388ff;stroke:black;stroke-width:2;fill-opacity:0.6;stroke-opacity:1" /></svg>';
            break;       
        default:
            // circle
            symbolsvg = '<svg width="20" height="20"><circle cx="10" cy="10" r="9" style="fill:#3388ff;stroke:black;stroke-width:2;fill-opacity:0.6;stroke-opacity:1" /></svg>';
    };
    var fillc;
    for (var i = 0; i < grades.length; i++) {
    from = grades[i];
    to = grades[i + 1];
    fillc = getColor(from + 1);
    labels.push(
        symbolsvg.replace('#3388ff',fillc) + ' ' + from + (to ? '&nbsp;&ndash;&nbsp;' + to : '+'));
    }

    div.innerHTML = fieldname + "<br>";
    div.innerHTML += labels.join('<br>');
    return div;
}

// for source
function sourceOnEachFeature(feature, layer) {
    //bind click
    layer.on('click', function (e) {
      var target_id = sourceselection.indexOf(e.target)
      if (target_id >=0 ) {e.target.setStyle(source_shapeMakerOptions);sourceselection.splice(target_id,1);}
      else {e.target.setStyle({weight:3,color:"black",radius:sourceRadius + 3});
            sourceselection.push(e.target);}
      //document.dispatchEvent(new Event("source-selection-change"));
    })};

// for sinks (points)
// for sinks
function sinkOnEachFeature(feature, layer) {
    //bind click
    layer.on('click', function (e) {
        var target_id = sinkselection.indexOf(e.target)
        if (target_id >=0 ) {e.target.setStyle({weight:1,color:'grey',fillOpacity:0.8,radius:sinkRadius});sinkselection.splice(target_id,1);}
        else {e.target.setStyle({weight:2,color:"black",fillOpacity:1,radius:sinkRadius+2});
              sinkselection.push(e.target);}
        //document.dispatchEvent(new Event("sink-selection-change"));
    })
};

function onEachFeatureClosure(popup_fields) {
    return function onEachFeature(feature, layer) {
        var content_str="<strong>Sink: <br>"
        for (entry of popup_fields) {
            content_str += entry + ": " + feature.properties[entry] + "<br>";
        }
        content_str += "</strong>";
        layer.bindTooltip(content_str);
        layer.on('click', function (e) {
            var target_id = sinkselection.indexOf(e.target)
            if (target_id >=0 ) {e.target.setStyle({weight:1,color:"grey",fillOpacity:0.7});sinkselection.splice(target_id,1);}
            else {e.target.setStyle({weight:2,color:"black",fillOpacity:1});
                  sinkselection.push(e.target);}
            document.dispatchEvent(new Event("sink-selection-change"));
        })
    }
}

// turn on/off layer
function handleclick(id){
    if (map.hasLayer(maplayers[id])) {
        map.removeLayer(maplayers[id]);
        $("#"+id).prop('checked', false);
    } else {
        maplayers[id].addTo(map);
        $("#"+id).prop('checked', true);
    }
}

 // Defining async function 
 async function getdata(url) { 
    
    // Storing response 
    const response = await fetch(url); 
    
    // Storing data in form of JSON 
    var data = await response.json(); 
    //console.log(data);
    return data;
} 

// load data by url
async function addcasedata(datadesc,dataurl,datastyle,popup_fields,datasymbol) {
    var data = await getdata(dataurl);
    // Add dataset_id to feature properties so we tie a source/sink back to its dataset
    for (let feature of data.features) {
        feature.properties.dataset_id = datadesc['dataid'];
    }
    
    var newLayer;
    if (!popup_fields || popup_fields.length === 0) {
        popup_fields = ["Name"];
    }

    if (datadesc['type'] == 'source') {
        // change symbol
        source_shapeMakerOptions['shape'] = datasymbol;
        newLayer = new L.geoJSON(data,{
            pointToLayer: function (feature, latlng) {
            var content_str="<strong>Source: <br>"
            for (entry of popup_fields) {
                content_str += entry + ": " + feature.properties[entry] + "<br>";
            }
            content_str += "</strong>";
            //var mymarker = L.circleMarker(latlng, geojsonMarkerOptions);
            var mymarker = L.shapeMarker(latlng, source_shapeMakerOptions);
            mymarker.bindTooltip(content_str);
            return mymarker;       
          },
          onEachFeature: sourceOnEachFeature,
        });

    } else if (datadesc['type'] == 'sink') {
        // load sink data
        // change sink symbol
        sink_shapeMakerOptions['shape'] = datasymbol;
        newLayer = new L.geoJSON(data,{
            pointToLayer: function (feature, latlng) {
            var content_str="<strong>Sink: <br>"
            for (entry of popup_fields) {
                content_str += entry + ": " + feature.properties[entry] + "<br>";
            }
            content_str += "</strong>";
            var color_value = feature.properties[datastyle];
            var fillcolor = getColor(color_value);
            //var mymarker = L.circleMarker(latlng, sinkMarkerOptions);
            var mymarker = L.shapeMarker(latlng, sink_shapeMakerOptions);
            mymarker.setStyle({'fillColor':fillcolor});
            mymarker.bindTooltip(content_str);
            return mymarker;       
          },
          onEachFeature: sinkOnEachFeature,
        });
       
        // newLayer = new L.geoJSON(data, {style: function(feature){
        //     var color_value = feature.properties[datastyle];
        //     var fillcolor = getColor(color_value); 
        //     return {'color':'grey','weight':1,'fillColor':fillcolor,'fillOpacity': 0.5,pane: "polygonsPane"};
        //   },
        //   onEachFeature: onEachFeatureClosure(popup_fields),
        // });
    }
    else {
        newLayer = new L.geoJSON(data);
    }

    var radiostr='<input class="form-check-input"  type="radio" id="'+datadesc['dataid']+'" checked="checked" onclick=handleclick(this.id)>';
    radiostr += '<label class="form-check-label" for="'+datadesc['dataid']+'">'+ datadesc['type'].charAt(0).toUpperCase() + datadesc['type'].slice(1)+":"+datadesc['name']+'</label><br>';
    
    $('#layercontrol').append(radiostr);
    // add selector
    if (datadesc['type'] == 'source') {
        var selector = '<select class="selectpicker" id="selector_' + datadesc['dataid'] +'" title="select by names ..." data-live-search="true" multiple data-actions-box="true" data-width="auto">';
        var ukey, uvalue;
        for (entry of data['features']) {
            ukey = entry['properties']['ID'];
            uvalue = entry['properties']['NAME'].toString().trim();
            // pick up first 15 
            if (uvalue.length > 20) {uvalue = uvalue.slice(0,20) + "...";}
            selector += '<option value="'+ ukey +'">'+ uvalue +'</option>';
            }
        selector += "</select>";
        $('#layercontrol').append(`<div>${selector}</div>`);
        // Activate bootstrap-select plugin
        $('#selector_' + datadesc['dataid']).selectpicker();
    }

    newLayer.addTo(map);
    maplayers[datadesc['dataid']] = newLayer;
    // ignore the source style for now
    if (datastyle && datadesc['type'] != 'source') {       // generate legend
            var legend = createLegend(datastyle,datasymbol);
            document.getElementById("layercontrol").appendChild(legend);   
        } 
       
}

// load cost surface
function addcostsurface(bbox) {
    //load default national cost surface
    var cost_image_url="https://simccs.org/geoserver/ows?service=WCS&version=2.0.0&request=GetCoverage&coverageId=SimCCS__cost&format=png";
    // &subset=Lat(29.920588,33.381122)&subset=Long(-89.251876,-83.277539)";
    // get bounds from feature group
    var allvectorlayers = [];
    for (let [key, value] of Object.entries(maplayers)) {
        allvectorlayers.push(value); }
    var vectorGroup = L.featureGroup(allvectorlayers);
    var vecb = vectorGroup.getBounds();
    //"BBOX": [-89.91, 38.1, -87.7, 40.9]}}
    // BBOX: [west, south, east, north]
    bbox = [vecb.getWest(),vecb.getSouth(),vecb.getEast(),vecb.getNorth()];
    allvectorlayers = null;
    vectorGroup = null;
    cost_image_url += "&subset=Lat(" +(bbox[1]-0.2) +","+(bbox[3]+0.2) +")";
    cost_image_url += "&subset=Long("+(bbox[0]-0.2) + ","+(bbox[2]+0.2) + ")";
    var cost_image_bounds = [[bbox[1]-0.2,bbox[0]-0.2],[bbox[3]+0.2,bbox[2]+0.2]];
    var costsurface = L.imageOverlay(cost_image_url,cost_image_bounds).addTo(map);
    var radiostr='<input class="form-check-input"  type="radio" id="costsurface" checked="checked" onclick=handleclick(this.id)>';
    radiostr += '<label class="form-check-label" for="costsurface">Cost Surface</label><br>';
    $('#layercontrol').append(radiostr);
    maplayers['costsurface'] = costsurface;
    //zoom map to the cost surface
    map.fitBounds(costsurface.getBounds());
}

// clear the selected
function clear_selection(needconfirm=true) {
    // clear all selected 
    var r;
    if (needconfirm) { 
        r = confirm("Clear all the selected?");
        // do nothing if cancelled
        if (r == false) {return;} }
    // clear selected sources
    var elayer;
    for (elayer of sourceselection) {
        elayer.setStyle(source_shapeMakerOptions);
    }
    sourceselection = [];
    //document.dispatchEvent(new Event("source-selection-change"));
    // clear selected sinks
    for (elayer of sinkselection) {
          elayer.setStyle({weight:1,color:'grey',fillOpacity:0.8,radius:sinkRadius});
    }
    sinkselection = [];
    //document.dispatchEvent(new Event("sink-selection-change"));
}

// source selector 
function source_selectbynames(dataid,selected_ids) {
    var elayer;
    // first handle deselect all 
    if (selected_ids.length == 0) {
      for (elayer of sourceselection) {
        elayer.setStyle(source_shapeMakerOptions);
          }
       sourceselection = [];
       return;
    }
    var source_id;
    var sourceLayer = maplayers[dataid];
    sourceLayer.eachLayer(function(layer) {
          // convert id to string object
          source_id = layer.feature.properties['ID'].toString();
          // check if layer already in selection
          var target_id = sourceselection.indexOf(layer);
          if (selected_ids.includes(source_id)) {
                // if not selected, add to selection
                if (target_id < 0) {layer.setStyle({weight:3,color:"black",radius:sourceRadius + 3});
                sourceselection.push(layer);}
          } else {
                // if deselected, remove it
                if (target_id >= 0) {
                      layer.setStyle(source_shapeMakerOptions);
                      sourceselection.splice(target_id,1);
                }
          }
    });

}

// hideunselected 
// rmeove dyn layers, reset styles
function removedynlayers() {
    for (var key in dynmaplayers) { 
        if (map.hasLayer(dynmaplayers[key])) { 
            switch (key) {
                case "source_selection_layer":
                  dynmaplayers[key].setStyle(source_shapeMakerOptions);
                  break;
                case "sink_selection_layer":
                  dynmaplayers[key].setStyle({weight:1,color:'grey',fillOpacity:0.4});
                  break;
                default:
                  break;
              } 
            map.removeLayer(dynmaplayers[key]);}
    }
}

function hideunselected(source_selection, sink_selection,network='') {

    for (var key in maplayers) { 
        if (map.hasLayer(maplayers[key])) { map.removeLayer(maplayers[key]);}
    }
    removedynlayers();
    var source_selection_layer = L.featureGroup(source_selection);
    source_selection_layer.setStyle({weight:3,color:"black",radius:sourceRadius + 3});
    var sink_selection_layer = L.featureGroup(sink_selection);
    sink_selection_layer.setStyle({weight:2,color:"black",fillOpacity:0.7});
    source_selection_layer.addTo(map);
    sink_selection_layer.addTo(map);
    dynmaplayers['source_selection_layer'] = source_selection_layer;
    dynmaplayers['sink_selection_layer'] = sink_selection_layer;
    // candidate_network_layer
    if (! network=='') {
        network.addTo(map);
        dynmaplayers['candidate_network_layer'] = network;
    }
}

// refreshmap by panel
function refreshmap(p_id) {
    if (p_id.includes('scenario')) {
        //console.log(sourceselection_panel);
        if (candidatenetwork_panel.hasOwnProperty(p_id)) {
            hideunselected(sourceselection_panel[p_id],sinkselection_panel[p_id],network=candidatenetwork_panel[p_id]); }
        else {hideunselected(sourceselection_panel[p_id],sinkselection_panel[p_id]); }
    }
    if (p_id.includes('home')) {
        // remove dynlayers
        removedynlayers();
        // add layers backs
        for (var key in maplayers){ 
            if (!map.hasLayer(maplayers[key])) { maplayers[key].addTo(map);}
        } 
        clear_selection(needconfirm=false);      
    }

}

// generate candidate network
function generatecandidatenetwork(panelid) {
    
    var source_selection = sourceselection_panel[panelid];
    var sink_selection = sinkselection_panel[panelid];
    var sourcedata = generatesourcedata(source_selection);
    var sinkdata=generatesinkdata(sink_selection);
    var sourceIds = getSourceIds(source_selection);
    var sinkIds = getSinkIds(sink_selection);
    var formData = new FormData();
    formData.set('sources', sourcedata);
    formData.set('sinks', sinkdata);
    formData.set('dataset', "Lower48US");
    return AiravataAPI.utils.FetchUtils.post("/maptool/candidate-network/", formData).then(function( data ) {
        // Note: 'data' includes Sinks and Sources but since those are
        // already displayed I'm opting to only display the Network
        var candidateNetworkLayer = L.geoJSON(null, {style:{color:"blue",opacity:0.5,weight:4}});
        candidateNetworkLayer.clearLayers();
        candidateNetworkLayer.addData(data["Network"]);
        if (!map.hasLayer(candidateNetworkLayer)) {
              candidateNetworkLayer.addTo(map);
        }
        // save candidateNetworkLayer
        dynmaplayers['candidate_network_layer'] = candidateNetworkLayer;
        candidatenetwork_panel[panelid] = candidateNetworkLayer;
        candidatenetwork_cached[panelid] = data["CandidateNetwork"];
        
        //console.log(candidatenetwork_panel);
        // Cache the candidate network
        //Maptool.cachedCandidateNetwork = data["CandidateNetwork"];
        //Maptool.cachedCandidateNetworkSourceIds = sourceIds;
        //Maptool.cachedCandidateNetworkSinkIds = sinkIds;
        //document.dispatchEvent(new CustomEvent("candidate-network-loaded", {detail: data}));
        // disbale button bn_generatecandidatenetwork_'+ panelid
        // create a temp download link
        document.getElementById('bn_generatecandidatenetwork_'+ panelid).disabled = true; 
        var download_div = document.getElementById('download_candidatenetwork_'+ panelid);
        var downloadlink = createdownloadlink("candidatenetwork.geojson",JSON.stringify(candidateNetworkLayer.toGeoJSON()),"Download Candidatenetwork");
        download_div.appendChild(downloadlink);

        return data;
  }).catch(display_error_modal);
}

function getSourceIds(selections) {
    return new Set(selections.map(src => src.feature.properties.ID));
 }

 function getSinkIds(selections) {
    return new Set(selections.map(snk => "saline-" + snk.feature.properties.ID));
 }

function display_error_modal(error, message) {

    message = typeof message !== 'undefined' ? message : error.message;
    var m_html =`<div class="modal fade in" tabindex="-1" role="dialog">
<div class="modal-dialog" role="document">
<div class="modal-content">
<div class="modal-header">
<h5 class="modal-title">Error</h5>
<button type="button" class="close" data-dismiss="modal" aria-label="Close">
  <span aria-hidden="true">&times;</span>
</button>
</div>
<div class="modal-body">
<p class="error-message"></p>
</div>
<div class="modal-footer">
<button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
</div>
</div>
</div>
</div>`;
    $(m_html)
          .appendTo('body')
          .modal('show')
          .on('hidden.bs.modal', (e) => $(e.target).remove())
          .find(".error-message")
          .text(message);
}

function sswindowpicker_build() {
    // select sources and sinks by drawing
    var polygon_options = {
        showArea: false,
        shapeOptions: {
            stroke: true,
            color: 'black',
            weight: 2,
            opacity: 1,
            fill: true,
            fillColor: "orange", //same as color by default
            fillOpacity: 0.5,
            clickable: true,
            pane:"drawingPane"
        }
    };
    var drawnItems = new L.FeatureGroup();
    drawnItems.clearLayers();
    map.addLayer(drawnItems);
    map.once('draw:created', function (e) {  
        var count_source = 0, count_sink = 0;
        var count_sinklayer = 0;
        var draw_type = e.layerType,draw_layer = e.layer;
        
        // go through all the data sets
        Object.keys(datasets).forEach(function(key) {
            //key is case id
            if (map.hasLayer(maplayers[key])) {
                // find out case type
                // datasets[key]['type']
                //console.log(datasets[key]);
                if (datasets[key]['type'] == 'source') {
                    // empty sourceselection
                    sourceselection = [];
                    maplayers[key].eachLayer(function(layer) {
                        var contains = turf.inside(layer.toGeoJSON(), draw_layer.toGeoJSON());
                        if (contains){
                              layer.setStyle({weight:3,color:"black",radius:sourceRadius + 3});
                              sourceselection.push(layer); count_source +=1; } else {layer.setStyle(source_shapeMakerOptions);
                              }
                    });
                }
                if (datasets[key]['type'] == 'sink') {
                    //empty sinkselection only for the first sink layer
                    count_sinklayer += 1;
                    if (count_sinklayer == 1) {sinkselection = [];}
                    maplayers[key].eachLayer(function(layer) {
                          var contains = turf.inside(layer.toGeoJSON(), draw_layer.toGeoJSON());
                          if (contains){layer.setStyle({weight:2,color:"black",fillOpacity:1,radius:sinkRadius+2});
                          sinkselection.push(layer);count_sink +=1; } else {layer.setStyle({weight:1,color:'grey',fillOpacity:0.8,radius:sinkRadius});}
                    });
                }
            }
         });
        alert(count_source.toString() + " sources " + count_sink.toString() + " sinks are selected.");
        count_source = 0;
        count_sink = 0;
        drawnItems.clearLayers(draw_layer);
        map.removeLayer(drawnItems);
        polygonDrawer.disable();   
    }
    );
    var polygonDrawer = new L.Draw.Polygon(map, polygon_options);     
    polygonDrawer.enable();

}