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

var geojsonMarkerOptions = {
    radius: 8,
    fillColor: "red",
    color: "#000",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.8,
    pane: "pointsPane"
};

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

async function addcasedata(datadesc,dataurl,datasytle) {
    var data = await getdata(dataurl);
    var newLayer;
    if (datadesc['type'] == 'source') {
        newLayer = new L.geoJSON(data,{
            pointToLayer: function (feature, latlng) {
            var mymarker = L.circleMarker(latlng, geojsonMarkerOptions);
            return mymarker;       
          }
        });
    } else {
        newLayer = new L.geoJSON(data);
    }

    var radiostr='<input class="form-check-input"  type="radio" id="'+datadesc['dataid']+'" checked="checked" onclick=handleclick(this.id)>';
    radiostr += '<label class="form-check-label" for="'+datadesc['dataid']+'">'+datadesc['type'].toUpperCase()+":"+datadesc['name']+'</label><br>';
    
    document.getElementById("layercontrol").innerHTML+=radiostr;
    newLayer.addTo(map);
    maplayers[datadesc['dataid']] = newLayer;
}