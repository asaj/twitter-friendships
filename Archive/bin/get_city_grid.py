from osgeo import ogr
import json

POINTS_FILE = "../data/cambridge_points.json"
BOUNDARY_FILE = "../data/CAMBRIDGE_CITY_BOUNDARY.geojson"
CITY_CENTER = [42.373611, -71.110556]
BOUNDARY_SIZE = .1 # Approximately 7 miles
PITCH = .002 # .1 - .14 miles
PITCH_IN_MILES = ".2mi" # Should be larger than pitch by a little

boundary = ogr.Open(BOUNDARY_FILE, 0)
boundary_layer = boundary.GetLayer()
feature = boundary_layer.GetFeature(1)
geom = feature.GetGeometryRef()
center = geom.Centroid()

r = {"pitch":PITCH_IN_MILES}
points = []

for x in range (-1 * int(BOUNDARY_SIZE/PITCH), int(BOUNDARY_SIZE/PITCH)):
  for y in range (-1 * int(BOUNDARY_SIZE/PITCH), int(BOUNDARY_SIZE/PITCH)):
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(center.GetX() + (x * PITCH), center.GetY() + (y * PITCH))
    if geom.Intersects(point):
      points.append([point.GetX(), point.GetY()])
r["points"] = points
with open(POINTS_FILE, 'w') as outfile:
  json.dump(r, outfile)


