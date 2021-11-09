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


map_layercontrol = L.control.layers(null, null, { collapsed: false });
map_layercontrol.addTo(map);
map_solutionSummaryControl = null;
 
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
    fillOpacity: 0.8,
    color: "grey",
    weight:1,
    pane: "toppointsPane"
};

var sink_shapeMakerOptions = {
    radius: sinkRadius,
    shape: "square",
    fillColor: "blue",
    fillOpacity: 0.8,
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


function getcolor(featureValue,limits,colorlist){
    if (!isNaN(featureValue)) {
        // Find the bucket/step/limit that this value is less than and give it that color
        for (var i = 0; i < limits.length; i++) {
          if (featureValue <= limits[i]) {
            return colorlist[i]
            break
          }
        }
    }
}

// create a legend for coloring field
function createLegend(datasetid,fieldname,symbol,limits,colorlist)
{
    //var div = L.DomUtil.create('div', 'info legend'),
    var div = L.DomUtil.create('div'),
    labels = [],
    from, to;
    // legend_div: id_legend
    div.id = datasetid+"_legend";
    var symbolsvg;
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
    for (var i = 0; i < limits.length; i++) {
    from = limits[i];
    to = limits[i+1];
    fillc = colorlist[i];
    labels.push(
        symbolsvg.replace('#3388ff',fillc) + ' ' + from.toFixed(2) + (to ? '&nbsp;&ndash;&nbsp;' + to.toFixed(2) : '+'));
    }

    div.innerHTML = fieldname + "<br>";
    div.innerHTML += labels.join('<br>');
    return div;
}

// function show/hide legend
function showlegend(legendid) {
    var legenddiv = document.getElementById(legendid + "_legend");
    if (legenddiv.style.display == "none") 
    {
        legenddiv.style.display = "block";
    }
    else 
    {
        legenddiv.style.display = "none";
    }
}

// modify style of a given layer
function modifystyle(stylelayerid) {
    var legenddiv = document.getElementById(stylelayerid + "_legend");
    legenddiv.style.display = "none";
    var stylediv = document.getElementById(stylelayerid + "_style");

    const fieldlist=["fieldCap (MtCO2)","costFix ($M)","fixO&M ($M/yr)","wellCap (MtCO2/yr)",	"wellCostFix ($M)",	"wellFixO&M ($M/yr)","varO&M ($/tCO2)"];
    stylediv.innerHTML = "<label >Select field: </label>"
    var selectTag = document.createElement("SELECT");
    selectTag.id = stylelayerid + "_style_field";
    fieldlist.forEach(function(item, index, array) {
        var opt = document.createElement("option");
        opt.text = item;
        opt.value = item;
        selectTag.add(opt);
     });
     stylediv.appendChild(selectTag);

     const methodslist = [{label:'quantile',value:'q'},{label:"equidistant",value:'e'}];
     stylediv.innerHTML += "<br>"
     stylediv.innerHTML += "<label >Method: </label>"
     var selectmethod = document.createElement("SELECT");
     selectmethod.id = stylelayerid + "_style_method";
     methodslist.forEach(function(item, index, array) {
        var opt = document.createElement("option");
        opt.text = item.label;
        opt.value = item.value;
        selectmethod.add(opt);
     });
     stylediv.appendChild(selectmethod);

     stylediv.innerHTML += "<br>"
     stylediv.innerHTML += "<label >Steps: </label>"
     var selectstep = document.createElement("SELECT");
     selectstep.id = stylelayerid + "_style_step";
     for (let i = 3; i < 11; i++) { 
        var opt = document.createElement("option");
        opt.text = i.toString();
        opt.value = i.toString();
        selectstep.add(opt);
     }
     stylediv.appendChild(selectstep);
     stylediv.innerHTML += "<br>"
     stylediv.innerHTML += "<label >Colors: </label>"

     stylediv.innerHTML +="<br>";
     stylediv.innerHTML += '<button type="button" class="btn btn-primary btn-sm">Update Style</button>';
     stylediv.innerHTML += '<button type="button" class="btn btn-primary btn-sm">Cancel</button>';
     stylediv.innerHTML += "<br>";

    // show style
    stylediv.style.display = "block";

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

// function to caculate color map
function colormap(geojson,opts){
    var values = geojson.features.map(
        e=>e.properties[opts.valueProperty]
        );
        //console.log(values);
      var limits = chroma.limits(values, opts.mode, opts.steps - 1)
    //console.log(limits)
     var colorlist = (opts.colors && opts.colors.length === limits.length ?
                    opts.colors :
                    chroma.scale(opts.scale).colors(limits.length))
    //console.log(colors);
    return [limits,colorlist];
}

// load data by url
async function addcasedata(datadesc,dataurl,datastyle,popup_fields,datasymbol) {
    var data = await getdata(dataurl);
    // Add dataset_id and version to feature properties so we tie a source/sink back to its dataset
    for (let feature of data.features) {
        feature.properties.dataset_id = datadesc['dataid'];
        feature.properties.dataset_version = datadesc['current_version'];
    }
    
    var newLayer;
    var legend,limits,colorlist;
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
        // the default one is the data style
        // caculate the limits and color first
        var opts={};
        opts["valueProperty"] = datastyle;
        //q for quantile, e for equidistant, k for k-means
        mode = {"q":'quantile','e':'equidistant'};
        opts['mode']='q';
        opts['steps']= 10;
        opts['scale']= ['green','yellow','red'];
        opts['colors']=[];  
        [limits, colorlist] = colormap(data,opts);
        newLayer = new L.geoJSON(data,{
            pointToLayer: function (feature, latlng) {
            var content_str="<strong>Sink: <br>"
            for (entry of popup_fields) {
                content_str += entry + ": " + feature.properties[entry] + "<br>";
            }
            content_str += "</strong>";
            //var color_value = feature.properties[datastyle];
            //var fillcolor = getColor(color_value);
            var fillcolor = getcolor(feature.properties[opts.valueProperty],limits,colorlist);
            //var mymarker = L.circleMarker(latlng, sinkMarkerOptions);
            var mymarker = L.shapeMarker(latlng, sink_shapeMakerOptions);
            mymarker.setStyle({'fillColor':fillcolor});
            mymarker.bindTooltip(content_str);
            return mymarker;       
          },
          onEachFeature: sinkOnEachFeature,
        });
        legend = createLegend(datadesc['dataid'],datastyle,datasymbol,limits,colorlist);
    }
    else {
        newLayer = new L.geoJSON(data);
    }

    var radiostr='<input class="form-check-input"  type="radio" id="'+datadesc['dataid']+'" checked="checked" onclick=handleclick(this.id)>';
    radiostr += '<label class="form-check-label" for="'+datadesc['dataid']+'">'+ datadesc['type'].charAt(0).toUpperCase() + datadesc['type'].slice(1)+":"+datadesc['name']+"</label>";
    if (datastyle && datadesc['type'] != 'source') {
        radiostr += '<div style="margin-left: 10px;display: inline-block"; class="dropdown"> \
        <button class="btn btn-sm dropdown-toggle" type="button" data-toggle="dropdown"> \
        <span STYLE="font-size:18px">&#8286;</span></button> \
        <ul class="dropdown-menu"> \
          <li><a class="dropdown-item" onclick=showlegend('+datadesc['dataid']+') href="#">Show/Hide Legend</a></li> \
          <li><a class="dropdown-item" onclick=modifystyle('+datadesc['dataid']+') href="#">Modify Style</a></li> \
        </ul> \
      </div>';
    }
    radiostr += "<br>";
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
    if (datastyle && datadesc['type'] != 'source') {  
            // atach an empty div for modify style
            var stylediv = L.DomUtil.create('div');
            // legend_div: id_legend
            stylediv.id = datadesc['dataid'] + "_style";
            stylediv.style.display = "none";
            document.getElementById("layercontrol").appendChild(stylediv);
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
            map.removeLayer(dynmaplayers[key]);
            map_layercontrol.removeLayer(dynmaplayers[key]);
        }
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
    map_layercontrol.addOverlay(source_selection_layer, "Sources");
    sink_selection_layer.addTo(map);
    map_layercontrol.addOverlay(sink_selection_layer, "Sinks");
    dynmaplayers['source_selection_layer'] = source_selection_layer;
    dynmaplayers['sink_selection_layer'] = sink_selection_layer;
    // candidate_network_layer
    if (! network=='') {
        network.addTo(map);
        map_layercontrol.addOverlay(network, "Candidate Network");
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
        var candidateNetworkLayer = L.geoJSON(null, {style:{color:"black",opacity:0.6,weight:3}});
        candidateNetworkLayer.clearLayers();
        candidateNetworkLayer.addData(data["Network"]);

        if (!map.hasLayer(candidateNetworkLayer)) {
              candidateNetworkLayer.addTo(map);
              map_layercontrol.addOverlay(candidateNetworkLayer, "Candidate Network");
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

const MAX_DISPLAYED_RESULTS = 5;

async function display_experiment_result(experiment_id){
    // Assign label and color for solution
    if (solution_configs.size >= MAX_DISPLAYED_RESULTS) {
            throw Error(`Max number of displayed experiments is ${MAX_DISPLAYED_RESULTS}`);
    }
    const solution_config = {};
    const labels = Array.from(solution_configs.values()).map(v => v.label);
    for (const label of ["#1", "#2", "#3", "#4", "#5"]) {
            if (!labels.includes(label)) {
                solution_config.label = label;
                break;
            }
    }
    const colors = Array.from(solution_configs.values()).map(v => v.color);
    for (const color of ["green", "red", "blue", "orange", "purple"]) {
            if (!colors.includes(color)) {
                solution_config.color = color;
                break;
            }
    }
    // Load experiment-result and solution summary in parallel and
    // display them both if neither fails
    const [experimentResult, solutionSummary] = await Promise.all([
        // TODO: we already have these URLs
        AiravataAPI.utils.FetchUtils.get(
                `/maptool/experiment-result/${encodeURIComponent(experiment_id)}`
        ),
        AiravataAPI.utils.FetchUtils.get(
                `/maptool/solution-summary/${encodeURIComponent(experiment_id)}`,
        )
    ]);
    await add_experiment_result_to_map(experimentResult, experiment_id, solution_config);
    add_solution_summary(solutionSummary, solution_config);
    solution_configs.set(experiment_id, solution_config);
};

async function add_experiment_result_to_map(data, experiment_id, solution_config) {

    var result_networkLayer = new L.geoJSON(data["Network"],{style:{color:solution_config.color,opacity:0.7,weight:4,pane:"linesPane"},
    });
    // reset style
    // 0-0.25, 0.25-5, 5-7.5, 10
    result_networkLayer.eachLayer(function(layer) { 
        var fv = layer.feature.properties['Flow'];
        var lw = 1;
        if (fv <= 0.25) {lw = 1;}
        else if (fv>0.25 && fv <= 5) {lw = 2;}
        else if (fv > 5 && fv <= 7.5 ) {lw = 3;}
        else if (fv > 7.5 && fv <= 10) {lw = 4;}
        else if (fv > 10) {lw=5;}
        else {lw=1;}
        layer.setStyle({weight:Math.ceil(lw*1.5+1)});
    });
    result_solutionNetworkLayers.set(experiment_id, result_networkLayer);
    map.on('click', show_solution_network_popup);

    map.addLayer(result_networkLayer);
    map_layercontrol.addOverlay(result_networkLayer, `${solution_config.label} 
            <span style="background-color:${solution_config.color}; display: inline-block;
                margin-bottom: 2px; width: 2em; height: 4px; opacity: 0.7;"></span> Solution`);
    map.fitBounds(result_networkLayer.getBounds(), {
            // Account for sidebar (may need more than 460 to also account for
            // solution summary, but just accounting for sidebar seems good enough)
            paddingTopLeft: [460, 0]
    });
}

function add_solution_summary(solutionSummary, solution_config) {

    if (map_solutionSummaryControl === null) {
            map_solutionSummaryControl = L.control.solutionSummary({position: "topleft"});
    }
    map_solutionSummaryControl.addTo(map);
    map_solutionSummaryControl.addSolutionSummary(solution_config.label, solutionSummary);
}

/*
* show information about all solution networks at the point (solution
* networks may be overlapping)
*/
function show_solution_network_popup(e) {
    const point = turf.point([e.latlng.lng, e.latlng.lat]);
    const popup = [];
    for (const [experiment_id, solution_config] of Array.from(solution_configs.entries())) {
            const solutionNetworkLayer = result_solutionNetworkLayers.get(experiment_id);
            if (!map.hasLayer(solutionNetworkLayer)) {
                continue;
            }
            for (const layer of solutionNetworkLayer.getLayers()) {
                const feature = layer.toGeoJSON();
                const isOnLine = turf.booleanPointOnLine(point, feature, {epsilon: 1e-3});
                if (isOnLine) {
                        popup.push(`
                            <b>
                                    ${solution_config.label}
                                    <span style="background-color:${solution_config.color}; display: inline-block;
                                        margin-bottom: 2px; width: 2em; height: 4px; opacity: 0.7;"></span>
                                    Solution 
                            </b>
                            <br/>Flow: ${feature.properties.Flow}
                            <br/>Length (KM): ${feature.properties.LengKM}
                        `);
                }
            }
    }
    if (popup.length > 0) {
            map.openPopup(popup.join('<hr>'), e.latlng);
    }
}

function remove_experiment_result(experiment_id) {

    const result_solutionLayer = result_solutionNetworkLayers.get(experiment_id);
    if (result_solutionLayer) {
            map_layercontrol.removeLayer(result_solutionLayer);
            if (map.hasLayer(result_solutionLayer)) {
                map.removeLayer(result_solutionLayer);
            }
            result_solutionNetworkLayers.delete(experiment_id);
    }
    const solution_config = solution_configs.get(experiment_id);
    if (solution_config) {
        const experiment_label = solution_config.label;
        if (experiment_label) {
                map_solutionSummaryControl.removeSolutionSummary(experiment_label);
                solution_configs.delete(experiment_id);
                if (solution_configs.size === 0) {
                    map_solutionSummaryControl.remove();
                }
        }
    }
}
