var _case_study_state = {
    current_dataset_id: null
}

function get_current_dataset_id() {
    return _case_study_state.current_dataset_id;
}

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
    var legend_data=[];
    var datafolder = '/static/Scenarios/'+casefolder+'/';
    $.getJSON(datafolder + summaryjson,function(data){
        sources_json = data['inputs']['sources'];
        sinks_json = data['inputs']['sinks'];
        candidnetwork_json = data['inputs']['candidatenetwork'];
        _case_study_state.current_dataset_id = data['dataset-id'];

        //loading sources
        current_case['sources']= datafolder + sources_json;
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
        current_case['sinks']= datafolder + sinks_json;
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
                legend_data.push(['Sources','red']);
                legend_data.push(['Sinks','green']);
                legend_data.push(['Candidate Network','grey']);

                //loading solution network
        var display_colors = ['Blue','Green','Red','Yellow'];
        for (i = 0; i < data['results'].length; i++) {
            var result_network = data['results'][i]['network'];
            var result_case = data['results'][i]['case'];
            get_dynamiclayer_from_json(datafolder + result_network,result_case, display_colors[i]);
            legend_data.push([result_case,display_colors[i]]);
        }
        layercontrol.addTo(map);      
        //alert(legend_data);
        // display summary
        var case_summary = document.getElementById("case_stuides_display_summary");
        case_summary.innerHTML=data["summary"];
        var info_link = '<br><a href=url target=_><strong>More information</strong></a><br><br>';
        case_summary.innerHTML += info_link.replace('url',data['publication']);
        // generate legend
        var legend_div = document.getElementById("case_studies_legend");
        var legend_str = "<div><table>";
        legend_str += '<tr><td><span style="height:15px; width:15px; background-color:red;border-radius: 50%;display:inline-block;" /></td><td><strong>Sources</strong></td></tr>';
        legend_str += '<tr><td><span style="height:15px; width:15px; background-color:green;border-radius: 50%;display:inline-block;" /></td><td><strong>Sinks</strong></td></tr>';
        //legend_str +='<tr><td><hr style="border: 1px solid grey;width:20px" /></td><td>Candidate Network</td></tr>';
        // legend for lines        
        for (i=2; i<legend_data.length;i++) {
            var temp = '<tr><td><hr style="border: 2px solid ccolor;width:20px" /></td><td>nname</td></tr>';
            var res = (temp.replace('ccolor',legend_data[i][1])).replace('nname',legend_data[i][0]);
            legend_str += res;
        }
        legend_str +='</table></div>';
        legend_div.innerHTML = legend_str;
    })
}
