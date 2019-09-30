function get_dynamiclayer_from_json(jsonfile, casename, stylecolor) {
    var templayer;
    $.getJSON(jsonfile,function (data) {
        templayer = new L.geoJSON(data,{style:{color:stylecolor},pane:"linesPane"});
        templayer.addTo(map);
        //map.addLayer(result_networkLayer);
        layercontrol.addOverlay(templayer,casename);
    });
}

function display_case_study(casefolder, summaryjson){
    //var layercontrol = new L.control.layers();
    var sources_json,sinks_json,candidnetwork_json;
    var datafolder = '/static/Scenarios/'+casefolder+'/';
    $.getJSON(datafolder + summaryjson,function(data){
        sources_json = data['inputs']['sources'];
        sinks_json = data['inputs']['sinks'];
        candidnetwork_json = data['inputs']['candidatenetwork'];

        //loading sources
        $.getJSON(datafolder + sources_json,function (data) {
            var result_sourceLayer = new L.geoJSON(data, {
                pointToLayer: function (feature, latlng) {
                    //var mypopup = L.popup().setContent(content_str);
                    var mymarker = L.circleMarker(latlng,{radius: 8,fillColor: "red",
                    color: "#000",weight: 1,opacity: 1,fillOpacity: 1,pane:"pointsPane"});
                    //mymarker.bindPopup(mypopup);
                    return mymarker;       
                }
            });
            map.addLayer(result_sourceLayer);
            layercontrol.addOverlay(result_sourceLayer,"Sources");
        });
        
        //loading sinks
            $.getJSON(datafolder + sinks_json,function (data) {
                var result_sinkLayer = new L.geoJSON(data, {
                    pointToLayer: function (feature, latlng) {
                        //var mypopup = L.popup().setContent(content_str);
                        var mymarker = L.circleMarker(latlng,{radius: 8,fillColor: "green",
                            color: "#000",weight: 1,opacity: 1,fillOpacity: 1,pane:"pointsPane"});
                        //mymarker.bindPopup(mypopup);
                        return mymarker;       
                    }
                });
                map.addLayer(result_sinkLayer);
                layercontrol.addOverlay(result_sinkLayer,"Sinks");
            });
                //loading candidnetwork
                $.getJSON(datafolder + candidnetwork_json,function (data) {
                    var result_candidnetworkLayer = new L.geoJSON(data,{style:{color:"black",opacity:0.5,weight:2,pane:"linesPane"}});
                    map.addLayer(result_candidnetworkLayer);
                    layercontrol.addOverlay(result_candidnetworkLayer,"Candidate");
            
                });
        //loading solution network
        var display_colors = ['Blue','Green','Red','Yellow'];
        for (i = 0; i < data['results'].length; i++) {
            var result_network = data['results'][i]['network'];
            var result_case = data['results'][i]['case'];
            get_dynamiclayer_from_json(datafolder + result_network,result_case, display_colors[i]);
        }
        layercontrol.addTo(map);      
        
        // display summary
        var case_summary = document.getElementById("case_stuides_display_summary");
        case_summary.innerHTML=data["summary"];

    })
}
