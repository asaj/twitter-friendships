from osgeo import ogr
import json
import utils

POINTS_FILE = "../data/cambridge_points.json"
MA_NEIGHBORHOODS_FILE = "../data/MA_NEIGHBORHOODS.geojson"
CAMBRIDGE_NEIGHBORHOODS_FILE = "../data/CAMBRIDGE_NEIGHBORHOODS.geojson"
BBOX_FILE = "../data/bbox.json"
PITCH = .25

def state_neighborhoods_to_city_neighborhoods(city, state_neighborhoods_file, city_neighborhoods_file):
  r = {
  "type": "FeatureCollection",
  "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
  "features": []}
  state_neighborhoods = ogr.Open(state_neighborhoods_file, 0)
  layer = state_neighborhoods.GetLayer()
  for feature_num in range(layer.GetFeatureCount()):
    feature = layer.GetFeature(feature_num)
    feature_city = feature.GetFieldAsString(feature.GetFieldIndex("CITY"))
    if feature_city == city:
      r["features"].append(json.loads(feature.ExportToJson()))
  for i, feature in enumerate(r["features"]):
    feature["id"] = i
  with open(city_neighborhoods_file, 'w') as outfile:
    json.dump(r, outfile)
#geom = feature.GetGeometryRef()
#center = geom.Centroid()

def relax_circle(point, pitch, geom):
  print "relaxing " + str(point.GetY()) + "," + str(point.GetX())
  points = []
  if geom.Intersects(point):
    points.append(point)
    circles = utils.get_hexagonally_packed_circles([point.GetY(), point.GetX()], pitch)[1:]
    for circle in circles:
      point = ogr.Geometry(ogr.wkbPoint)
      point.AddPoint(circle[0][1], circle[0][0])
      points += relax_circle(point, pitch, geom)
  return points

def get_neighborhood_points(pitch, city_neighborhoods_file, neighborhood_points_file, bbox_file):
  points = {}
  r = {"pitch":pitch, "points":points}
  neighborhoods = ogr.Open(city_neighborhoods_file, 0)
  layer = neighborhoods.GetLayer()
  for feature_num in range(layer.GetFeatureCount()):
    feature = layer.GetFeature(feature_num)
    feature_neighborhood = feature.GetFieldAsString(feature.GetFieldIndex("NAME"))
    geom = feature.GetGeometryRef()
    center = geom.Centroid()
    point_in_geom = True
    stack = [[center.GetY(), center.GetX()]]
    neighborhood_points = []
    while len(stack) > 0:
      point = stack.pop()
      if not utils.point_in_list(point, neighborhood_points, .000000001):
        ogr_point = ogr.Geometry(ogr.wkbPoint)
        ogr_point.AddPoint(point[1], point[0])
        if geom.Intersects(ogr_point):
          neighborhood_points.append(point)
          circles = utils.get_hexagonally_packed_circles(point, pitch)
          for circle in circles:
            stack.append(circle[0])
    r["points"][feature_neighborhood] = neighborhood_points  
    print "Generated " + str(len(neighborhood_points)) + " points on a " + str(PITCH) + " mile grid for neighborhood " + feature_neighborhood
  #For http://www.darrinward.com/lat-long/?id=430756
  """
  """
  bbox = [[9999, 9999], [-9999, -9999]]
  for neighborhood in points.keys():
    for point in points[neighborhood]:
      print str(point[0]) + "," + str(point[1])
      if point[1] < bbox[0][0]:
        bbox[0][0] = point[1]
      if point[1] > bbox[1][0]:
        bbox[1][0] = point[1]
      if point[0] < bbox[0][1]:
        bbox[0][1] = point[0]
      if point[0] > bbox[1][1]:
        bbox[1][1] = point[0]
  bbox[0][0] -= .01
  bbox[0][1] -= .01
  bbox[1][0] += .01
  bbox[1][1] += .01
  with open(bbox_file, 'w') as outfile:
    json.dump(bbox, outfile)
  with open(neighborhood_points_file, 'w') as outfile:
    json.dump(r, outfile)

#state_neighborhoods_to_city_neighborhoods("Cambridge", MA_NEIGHBORHOODS_FILE, CAMBRIDGE_NEIGHBORHOODS_FILE) 
get_neighborhood_points(PITCH, CAMBRIDGE_NEIGHBORHOODS_FILE, POINTS_FILE, BBOX_FILE)


