from django.http import JsonResponse
import requests

def get_data(request):
    # TODO get the query parameters from request.GET dictionary
    # TODO return JsonResponse(...)
    geom = request.GET["geom"]
    geom = geom.replace("%20"," ")
    geom = geom.replace("%2C",",")
    cqlfilter = 'Intersects(the_geom,Polygon((' + geom + ")))"
    geoserver_url = "https://simccs.org/geoserver/SimCCS/ows"
    #service=WFS&version=1.0.0&request=GetFeature&maxFeatures=500&outputFormat=text%2Fjavascript&format_options=callback:loadjson';
    PARAMS = {'service':'WFS','version':'1.0.0','request':'GetFeature',
        'maxFeatures':500,'outputFormat':'application/json','typeName':'Sources_082819_SimCCS_Format',
        'cql_filter':cqlfilter}
    
    r = requests.get(url = geoserver_url, params = PARAMS) 
    # extracting data in json format 
    # Number of Sources: #
    # Capturable CO2 of Sources: # MtCO2/yr
    # Number of Sinks: #
    # Total Sink Capacity: # MtCO2
    data = r.json() 
    totalfeatures = data['totalFeatures']
    capturable = sum([x['properties']['Capturable'] for x in data['features']])

    return JsonResponse({'totalsource':totalfeatures,'capturable':capturable})
