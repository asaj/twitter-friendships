import math

"""
Returns the lat/lng point defined by a center, angle, and radius
"""
def get_point(center, radians, radius):
  r = [0, 0]
  r[0] = center[0] + miles_to_latitude(radius) * math.sin(radians) 
  r[1] = center[1] + miles_to_longitude(radius)* math.cos(radians) 
  return r

"""
Converts miles to degrees latitude in the city of Cambridge
"""
def miles_to_latitude(miles):
  return .01/0.691 * miles

"""
Converts miles to degrees longitude in the city of Cambridge
"""
def miles_to_longitude(miles):
  return .01/0.511 * miles

"""
Finds the 7 hexagonally packed circles inside the circle defined by point, radius.
Takes point as a lat/lng pair and radius in miles, returns a list of (point, radius)
tuples.
"""
def get_hexagonally_packed_circles(point, radius):
  packed_circles = [[point, radius / 3.0]]
  for d in range(6):
    rad = math.radians(d * 60)
    packed_circles.append([get_point(point, rad, radius * 2.0 / 3.0), radius / 3.0])
  return packed_circles

"""
Checks if a point is in a list (rounding errors)
"""
def point_in_list(point, array, tolerance):
  for p in array:
    if abs(point[0] - p[0]) < tolerance and abs(point[1] - p[1]) < tolerance:
      return True
  return False
