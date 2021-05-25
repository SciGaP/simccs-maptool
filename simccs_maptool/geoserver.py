from django.http import JsonResponse
import requests

def wfs_call(layername, cqlfilter):
    """ wfs call """
    geoserver_url = "https://simccs.org/geoserver/SimCCS/ows"
    #service=WFS&version=1.0.0&request=GetFeature&maxFeatures=500&outputFormat=text%2Fjavascript&format_options=callback:loadjson';
    PARAMS = {'service':'WFS','version':'1.0.0','request':'GetFeature',
        'maxFeatures':10000,'outputFormat':'application/json',
        'cql_filter':str(cqlfilter),'typeName':layername}
    r = requests.get(url = geoserver_url, params = PARAMS) 
    print(PARAMS['cql_filter'])
    print(r.url)
    data = r.json() 

    return data

def get_data(request):
    # TODO get the query parameters from request.GET dictionary
    # TODO return JsonResponse(...)
    geom = request.GET["geom"]
    method = request.GET["method"]
    if "cql_filter"  in request.GET:
        ex_filter = request.GET['cql_filter']
        ex_filter = ex_filter.replace("%20"," ")
    else:
        ex_filter = ''
    geom = geom.replace("%20"," ")
    geom = geom.replace("%2C",",")
    cqlfilter = 'Intersects(the_geom,Polygon((' + geom + ")))"
    if len(ex_filter)>0:
        cqlfilter = "(" + cqlfilter+ ") AND " + ex_filter
    #geoserver_url = "https://simccs.org/geoserver/SimCCS/ows"
    #service=WFS&version=1.0.0&request=GetFeature&maxFeatures=500&outputFormat=text%2Fjavascript&format_options=callback:loadjson';
    # PARAMS = {'service':'WFS','version':'1.0.0','request':'GetFeature',
    #     'maxFeatures':500,'outputFormat':'application/json','typeName':'Sources_082819_SimCCS_Format',
    #     'cql_filter':cqlfilter}
    
    
    if method == "count":
        # sources
        data = wfs_call('Sources_082819_SimCCS_Format',cqlfilter)
        # extracting data in json format 
        # Number of Sources: #
        # Capturable CO2 of Sources: # MtCO2/yr
        # Number of Sinks: #
        # Total Sink Capacity: # MtCO2
        totalfeatures = data['totalFeatures']
        capturable = sum([x['properties']['Capturable'] for x in data['features']])
        # sinks: Oil/Gas Reservoir
        data = wfs_call('NATCARB_OG_Test',cqlfilter)
        totalsink_og = data['totalFeatures']
        sinkcapacity_og = sum([x['properties']['VOL_LOW'] for x in data['features']])
        # sinks Saline Formation
        #cqlfilter = cqlfilter.replace("the_geom","wkb_geometry")
        data = wfs_call('sco2t_national_v1_10k',cqlfilter)
        totalsink_saline = data['totalFeatures']
        sinkcapacity_saline = sum([x['properties']['fieldCap_M'] for x in data['features']])
        return JsonResponse({'totalsource':totalfeatures,'capturable':capturable,'totalsink_og':totalsink_og,'sinkcapacity_og':sinkcapacity_og,'totalsink_saline':totalsink_saline,'sinkcapacity_saline':sinkcapacity_saline})

    if method == "data":
        layer = request.GET["layer"]
        if layer == 'source': 
            #cqlfilter = 'Intersects(the_geom,Polygon((' + geom + ")))"
            data = wfs_call('Sources_082819_SimCCS_Format',cqlfilter)
        if layer == 'sink_saline':
            #cqlfilter = 'Intersects(the_geom,Polygon((' + geom + ")))"
            data = wfs_call('sco2t_national_v1_10k',cqlfilter)
        if layer == 'sink_og':
            #cqlfilter = 'Intersects(the_geom,Polygon((' + geom + ")))"
            data = wfs_call('NATCARB_OG_Test',cqlfilter)
        return JsonResponse(data)
