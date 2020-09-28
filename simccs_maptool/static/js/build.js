//load deafult map
map = L.map('map',{cursor:true}).setView([32.00,-85.43], 6);

//google streets
osm = new L.tileLayer('http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',{
    maxZoom: 20,
    subdomains:['mt0','mt1','mt2','mt3']
}).addTo(map);

var baseLayers = {
    "Google Street": osm
};

//create panes
map.createPane("polygonsPane");
map.createPane("linesPane");
map.createPane("pointsPane");

 // create the sidebar instance and add it to the map
 var sidebar = L.control.sidebar({ autopan: true, container: 'sidebar' }).addTo(map);
 
 // Defining async function 
async function getdata(url) { 
    
    // Storing response 
    const response = await fetch(url); 
    
    // Storing data in form of JSON 
    var data = await response.json(); 
    //console.log(data);
    return data;
} 

// default point option
var geojsonMarkerOptions = {
    radius: 8,
    fillColor: "red",
    color: "#000",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.8,
    pane: "pointsPane"
};

// function getcolor
function getColor(d) {
    return d > 10.0 ? '#f50000' :
            d > 5.0  ? '#fdff00' :
            d > 0.0  ? '#00f905' :
                        '#FFEDA0';
}
function createLegend(fieldname)
{
    var div = L.DomUtil.create('div', 'info legend'),
    grades = [0, 5, 10],
    labels = [],
    from, to;

    for (var i = 0; i < grades.length; i++) {
    from = grades[i];
    to = grades[i + 1];

    labels.push(
        '<i style="background:' + getColor(from + 1) + '"></i> ' +
        from + (to ? '&nbsp;&ndash;&nbsp;' + to : '+'));}

    div.innerHTML = fieldname + "<br>";
    div.innerHTML += labels.join('<br>');
    return div;
}

function onEachFeatureClosure(popup_fields) {
    return function onEachFeature(feature, layer) {
        var content_str="<strong>Sink: <br>"
        for (entry of popup_fields) {
            content_str += entry + ": " + feature.properties[entry] + "<br>";
        }
        content_str += "</strong>";
        layer.bindTooltip(content_str);
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

// load data by url
async function addcasedata(datadesc,dataurl,datastyle,popup_fields) {
    var data = await getdata(dataurl);
    var newLayer;
    if (popup_fields == "") {
        popup_fields = ["Name"];
    }

    if (datadesc['type'] == 'source') {
        newLayer = new L.geoJSON(data,{
            pointToLayer: function (feature, latlng) {
            var content_str="<strong>Source: <br>"
            for (entry of popup_fields) {
                content_str += entry + ": " + feature.properties[entry] + "<br>";
            }
            content_str += "</strong>";
            var mymarker = L.circleMarker(latlng, geojsonMarkerOptions);
            mymarker.bindTooltip(content_str);
            return mymarker;       
          }
        });
    } else if (datadesc['type'] == 'sink') {
        // load sink data
        newLayer = new L.geoJSON(data, {style: function(feature){
            var color_value = feature.properties[datastyle];
            var fillcolor = getColor(color_value); 
            return {'color':'grey','weight':1,'fillColor':fillcolor,'fillOpacity': 0.5,pane: "polygonsPane"};
          },
          onEachFeature: onEachFeatureClosure(popup_fields),
        });
    }
    else {
        newLayer = new L.geoJSON(data);
    }

    var radiostr='<input class="form-check-input"  type="radio" id="'+datadesc['dataid']+'" checked="checked" onclick=handleclick(this.id)>';
    radiostr += '<label class="form-check-label" for="'+datadesc['dataid']+'">'+ datadesc['type'].charAt(0).toUpperCase() + datadesc['type'].slice(1)+":"+datadesc['name']+'</label><br>';
    
    document.getElementById("layercontrol").innerHTML+=radiostr;
    newLayer.addTo(map);
    maplayers[datadesc['dataid']] = newLayer;
    if (datastyle !== "") {       // generate legend
            var legend = createLegend(datastyle);
            document.getElementById("layercontrol").appendChild(legend);   
        } 
       
}

// load cost surface
function addcostsurface(bbox) {
    //load default national cost surface
    var cost_image_url="https://simccs.org/geoserver/ows?service=WCS&version=2.0.0&request=GetCoverage&coverageId=SimCCS__cost&format=png";
    // &subset=Lat(29.920588,33.381122)&subset=Long(-89.251876,-83.277539)";
    //"BBOX": [-89.91, 38.1, -87.7, 40.9]}}
    cost_image_url += "&subset=Lat(" +(bbox[1]-0.2) +","+(bbox[3]+0.2) +")";
    cost_image_url += "&subset=Long("+(bbox[0]-0.2) + ","+(bbox[2]+0.2) + ")";
    var cost_image_bounds = [[bbox[1]-0.2,bbox[0]-0.2],[bbox[3]+0.2,bbox[2]+0.2]];
    var costsurface = L.imageOverlay(cost_image_url,cost_image_bounds).addTo(map);
    var radiostr='<input class="form-check-input"  type="radio" id="costsurface" checked="checked" onclick=handleclick(this.id)>';
    radiostr += '<label class="form-check-label" for="costsurface">Cost Surface</label><br>';
    document.getElementById("layercontrol").innerHTML+=radiostr;
    maplayers['costsurface'] = costsurface;
}