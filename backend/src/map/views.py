from django.http import HttpResponse, JsonResponse, FileResponse
from django.template.response import TemplateResponse
from django.http.request import HttpRequest
from map.models import Manufacturers, GeoIndication
from django.core import serializers
from django.middleware.csrf import get_token
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from os import path
from django.shortcuts import render
import sys
from django.template.loader import render_to_string

from django.views.decorators.csrf import csrf_exempt
import json

sys.path.insert(1, '..')
from define_class import define_class
from define_geo_by_id import find_locs, normalizeGeoLocation, define_coords


def create_csrf_token(request: HttpRequest) -> JsonResponse:
    return JsonResponse({'csrfToken': get_token(request)})


@csrf_exempt
def get_goods(request):
    s = serializers.serialize('json', GeoIndication.objects.all())

    return HttpResponse(s, content_type='json')


@csrf_exempt
def get_indications_names(request):
    names = list(GeoIndication.objects.values_list('name', flat=True))
    return JsonResponse(names, safe=False)


@csrf_exempt
def get_indications_classes(request):
    classes = list(GeoIndication.objects.values_list('target', flat=True))
    classes_uniq = list(set(classes))
    return JsonResponse(classes_uniq, safe=False)


@csrf_exempt
def get_polygons_by_facets(request):
    data = json.loads(request.body)
    names = data['names']
    types = data['types']

    query = GeoIndication.objects.all()
    if names:
        query = query.filter(name__in=names)
    if types:
        query = query.filter(target__in=types)

    query = query.values_list('geo_loc_polygon', 'id')

    respond = list(query)

    if names or types:
        return JsonResponse(respond, safe=False)

    return JsonResponse('', safe=False)


@csrf_exempt
def get_ids_product(request):
    data = json.loads(request.body)
    names = data['names']
    types = data['types']

    query = GeoIndication.objects.all()
    if names:
        query = query.filter(name__in=names)
    if types:
        query = query.filter(target__in=types)

    query = query.values_list('id', flat=True)

    respond = list(query)

    if names or types:
        return JsonResponse(respond, safe=False)

    return JsonResponse('', safe=False)


@csrf_exempt
def get_info(request):
    idMain = json.loads(request.body)
    query = Manufacturers.objects.filter(mainId__in=idMain)
    geo = GeoIndication.objects.all()
    # geo_main = geo.values_list('id', 'geo_loc_original')
    # print(geo_main)
    query = list(query.values_list('description',
                                   'href',
                                   'mainId',
                                   'manufacturer',
                                   'status'))

    dict_query = {}

    for i in range(len(query)):
        q = query[i]
        if q[2] not in dict_query:
            dict_query[q[2]] = []

        geo_main = geo.filter(id=q[2])
        dict_query[q[2]].append({
            "description": q[0],
            "href": q[1],
            "mainId": q[2],
            "manufacturer": q[3],
            "name": geo_main.values_list('name')[0],
            "status": q[4],
            "main_geo_text": geo_main.values_list('geo_loc_original')[0],
            "main_href": geo_main.values_list('href')[0],
            "main_description": geo_main.values_list('description')[0]
        })

    for idOne in idMain:
        numId = int(idOne)
        if numId not in dict_query:
            name = geo.filter(id=numId).values_list('name', 'id', 'geo_loc_original', 'href', 'description')[0]
            dict_query[numId] = [{
                "name": name[0],
                "mainId": name[1],
                "main_geo_text": name[2],
                "main_href": name[3],
                "main_description": name[4],
            }]

    return JsonResponse(dict_query, safe=False)


@csrf_exempt
def get_image_for_product(request):
    key = json.loads(request.body)

    print(key)

    for ext in ['.png', '.jpg', '.jpeg']:
        pathImage = f'media/imgs/{key}{ext}'
        if path.exists(pathImage):
            return FileResponse(open(pathImage, 'rb'))

    return FileResponse(open(f'media/imgs/placeholder.jpg', 'rb'))


def is_point_in_poly(point, poly):
    for i in range(len(poly)):
        arrPoints = []
        for j in range(len(poly[i])):
            arrPoints.append((poly[i][j]['lat'], poly[i][j]['lng']))

        polygon = Polygon(arrPoints)

        if polygon.contains(point):
            return True

    return False


def is_point_in_object(lat, lng, poly):
    polyDict = eval(poly)
    keys = polyDict.keys()
    point = Point(lat, lng)

    for key in keys:
        if is_point_in_poly(point, polyDict[key]['poly']):
            return True

    return False


@csrf_exempt
def check_polygons(request):
    data = json.loads(request.body)

    lat = data['lat']
    lng = data['lng']

    resultNames = []

    geo = GeoIndication.objects.values_list('name', 'geo_loc_polygon')

    for i in range(len(geo)):
        if is_point_in_object(lat, lng, geo[i][1]):
            resultNames.append(geo[i][0])

    return JsonResponse(resultNames, safe=False)


@csrf_exempt
def define_geo_polygon(request):
    #     text_area = json.loads(request.body)
    #
    #     bert = find_locs(text_area)
    #
    #     print(bert)
    #
    return JsonResponse('', safe=False)


@csrf_exempt
def find_and_normalize(request):
    id_object = request.POST['id-nmpt']
    try:
        df = GeoIndication.objects.get(id=id_object)
        arrayLocs = find_locs(df.geo_loc_original)
        arrayNormLocs = normalizeGeoLocation(arrayLocs)
    except:
        return JsonResponse(None, safe=False)

    return JsonResponse(arrayNormLocs, safe=False)


@csrf_exempt
def find_coords(request):
    request_objects = request.POST.dict()
    id_object = request_objects['id-nmpt']
    array = []
    for key, value in request_objects.items():
        if key.startswith('add'):
            array.append(value)
    polyObject, arr_label_to_show = define_coords(array)

    df = GeoIndication.objects.get(id=id_object)
    df.geo_loc_polygon = polyObject
    df.save()

    return JsonResponse(arr_label_to_show, safe=False)


@csrf_exempt
def form_page(request):
    return render(request, 'add_poly_form.html', {})


@csrf_exempt
def classify_empty(request):
    df = GeoIndication.objects.all()
    emptySet = df.filter(target='')
    nullSet = df.filter(target__isnull=True)
    dict_changed = {}

    for item in emptySet:
        defined = define_class(item.description)
        item.target = defined
        item.save()
        dict_changed[item.name] = defined

    for item in nullSet:
        defined = define_class(item.description)
        item.target = defined
        item.save()
        dict_changed[item.name] = defined

    return TemplateResponse(request, 'classify.html', context={'data': dict_changed})
