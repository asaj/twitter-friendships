"""
Want all twitter users in cambridge and a list of the people they follow?

"""
from __future__ import unicode_literals
import requests
from requests_oauthlib import OAuth1
from urlparse import parse_qs
import json
import time
from osgeo import ogr

REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize?oauth_token="
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"

CONSUMER_KEY = "DLb9PnyxjhTwG0aykAFrR9Hfr"
CONSUMER_SECRET = "NbMTJTtjE0fVelwHxxpm1Hnj3t1M36d3Gajum16Q4SQhNaHKNX"

OAUTH_TOKEN = "431180881-U0Ywdjf8AZCdaPfZASAvHOtcKN3bRA0lHePxzE9e"
OAUTH_TOKEN_SECRET = "tk9BDjzVfTiGXbR3dgaV241Z24Hb0oAaDgdqpzxWQndmp"

CAMBRIDGE_POINTS_FILE = "../data/cambridge_points.json"
USED_QUERIES_FILE = "../data/used_queries.json"
#used_queries = json.loads(open(USED_QUERIES_FILE).read())
USED_URLS_FILE = "../data/used_urls.json"
used_urls = json.loads(open(USED_URLS_FILE).read())
LIMIT_EXCEEDED_URLS_FILE = "../data/limit_exceeded_urls.json"
limit_exceeded_urls = json.loads(open(LIMIT_EXCEEDED_URLS_FILE).read())

#queries = ["the", "i", "to", "a", "and", "is", "in", "it", "you", "of",
#           "tinyurl.com", "for", "on", "my", "%27s", "that", "at", "with", "me", "do",
#           "have", "just", "this", "be", "n%27t", "so", "are", "%27m", "not", "was"]
queries = []
queries.append("%20") 

USERS_FILE = "../data/cambridge_twitter_users.json"
users = json.loads(open(USERS_FILE).read())

FRIENDSHIPS_FILE = "../data/cambridge_twitter_friendships.json"
friendships = json.loads(open(FRIENDSHIPS_FILE).read())

def setup_oauth():
    """Authorize your app via identifier."""
    # Request token
    oauth = OAuth1(CONSUMER_KEY, client_secret=CONSUMER_SECRET)
    r = requests.post(url=REQUEST_TOKEN_URL, auth=oauth)
    credentials = parse_qs(r.content)

    resource_owner_key = credentials.get('oauth_token')[0]
    resource_owner_secret = credentials.get('oauth_token_secret')[0]

    # Authorize
    authorize_url = AUTHORIZE_URL + resource_owner_key
    print 'Please go here and authorize: ' + authorize_url

    verifier = raw_input('Please input the verifier: ')
    oauth = OAuth1(CONSUMER_KEY,
                   client_secret=CONSUMER_SECRET,
                   resource_owner_key=resource_owner_key,
                   resource_owner_secret=resource_owner_secret,
                   verifier=verifier)

    # Finally, Obtain the Access Token
    r = requests.post(url=ACCESS_TOKEN_URL, auth=oauth)
    credentials = parse_qs(r.content)
    token = credentials.get('oauth_token')[0]
    secret = credentials.get('oauth_token_secret')[0]

    return token, secret


def get_oauth():
    oauth = OAuth1(CONSUMER_KEY,
                client_secret=CONSUMER_SECRET,
                resource_owner_key=OAUTH_TOKEN,
                resource_owner_secret=OAUTH_TOKEN_SECRET)
    return oauth

"""
Searches the twitter API for tweets.  Searches each query at 
point "point" within radius "radius".  Returns a dictionary of the users found,
keyed by user_id.
"""
def get_geocode_twitter_users(point, radius, query, oauth):
  new_users = {}
  geocode = str(point[1]) + "," + str(point[0]) + "," + radius
  request_url = "https://api.twitter.com/1.1/search/tweets.json?q=" + query + "&geocode=" + geocode + "&count=100"
  if request_url in used_urls:
    pass
    #print "Already tried request " + request_url
    #return {}
  print "Trying request " + request_url
  r = requests.get(url=request_url, auth=oauth)

  # If we run out of requests, sleep for 30 minutes and try again
  while ('errors' in r.json().keys()):
    print "Found error in json response: \"" + r.json()["errors"][0]["message"]+ "\", sleeping for 15 minutes"
    time.sleep(15 * 60)
    r = requests.get(url=request_url, auth=oauth)

  print "Got " + str(len(r.json()["statuses"])) + " results" 
  # Extract users from tweets
  for status in r.json()["statuses"]:
    user_id = status["user"]["id"]
    if user_id not in users.keys():
      new_users[user_id] = status["user"]
  if request_url not in used_urls:
    used_urls.append(request_url)
    with open(USED_URLS_FILE, 'w') as outfile:
      json.dump(used_urls, outfile)
  return (new_users, r.json() > 99)

def miles_to_latitude(miles):
  return .01/0.691 * miles

def miles_to_longitude(miles):
  return .01/0.511 * miles
  

def get_point(center, radians, radius):
  center[0] = center[0] + miles_to_latitude(radius) * math.sin(radians) 
  center[1] = center[1] + miles_to_longitude(radius)* math.cos(radians) 
  return center


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
  print packed_circles
  return packed_circles

def relax_circle(point, radius, query, oauth):
  (new_users, recurse) = get_geocode_twitter_users(point, radius, query, oauth)
  if recurse:
    print "Results exceeded limit, querying hexagonally packed circles"
    for circle in get_hexagonally_packed_circles(point, radius):
      new_users.update(relax_circle(circle[0], circle[1], query, oauth)) 
  return new_users
    
    
def get_cambridge_twitter_users():
  if not OAUTH_TOKEN:
    token, secret = setup_oauth()
    print "OAUTH_TOKEN: " + token
    print "OAUTH_TOKEN_SECRET: " + secret
  else:
    oauth = get_oauth()
    cambridge_points = json.loads(open(CAMBRIDGE_POINTS_FILE).read())["points"]
    radius = json.loads(open(CAMBRIDGE_POINTS_FILE).read())["pitch"]
    print "Searching " + str(len(cambridge_points)) + " points for cambridge twitter users"
    for (i, point) in enumerate(cambridge_points):
      for query in queries: 
        new_users = relax_circle(point, radius, query, oauth)
        if len(new_users.keys()) > 0:
          count = 0
          for user in new_users.keys():
            if user not in users.keys():
              users[user] = new_users[user]
              count += 1
          if count > 0:
            print "Found " + str(count) + " new users"
            with open(USERS_FILE, 'w') as outfile:
              json.dump(users, outfile)


def get_cambridge_twitter_friendships(user_ids):
  if not OAUTH_TOKEN:
    token, secret = setup_oauth()
    print "OAUTH_TOKEN: " + token
    print "OAUTH_TOKEN_SECRET: " + secret
  else:
    oauth = get_oauth()
    print "Finding friendships for " + str(len(user_ids)) + " cambridge twitter users"
    print "Already have friendships for " + str(len(friendships.keys())) + " cambridge twitter users"
    for (i, user_id) in enumerate(user_ids):
      if (user_id in friendships.keys()):
        print "Already found friendhips for user " + user_id + "  " + str(i) + "/" + str(len(user_ids))
        continue
      cursor = -1
      friends = []
      while True:
        request_url = "https://api.twitter.com/1.1/friends/ids.json?cursor=" + str(cursor) + "&user_id=" + user_id + "&count=5000" 
        print "URL: " + request_url
        r = requests.get(url=request_url, auth=oauth)

        # If we run out of requests, sleep for 30 minutes and try again
        while ('errors' in r.json().keys()):
          print "Found error in json response: \"" + r.json()["errors"][0]["message"]+ "\", sleeping for 15 minutes"
          time.sleep(15 * 60)
          r = requests.get(url=request_url, auth=oauth)
        friends += r.json()["ids"]
        cursor = r.json()["next_cursor"]
        if cursor == 0:
          break
      friendships[user_id] = friends
      with open(FRIENDSHIPS_FILE, 'w') as outfile:
        json.dump(friendships, outfile)
      print "Found " + str(len(friends)) + " friends for user " + user_id

def create_graph_from_users_and_friendships(users, friendships, graph_path):
  graph = {}
  nodes = []
  for user in users.keys():
    nodes.append({"group": 1, "name": str(user)})
  graph["nodes"] = nodes
  links = []
  print "Creating graph for " + str(len(users.keys())) + " twitter users"
  for user in users.keys():
    if user not in friendships.keys():
      continue
    for friend in friendships[user]:
      if str(friend) in users.keys():
        links.append({"source": nodes.index({"group":1, "name":str(user)}), "target":nodes.index({"group":1, "name":str(friend)}), "type":"friendship", "value":1})
        print "Found friendship between " + str(user) + " and " + str(friend)
  graph["links"] = links
  print "Found " + str(len(links)) + " edges"
  with open(graph_path, 'w') as outfile:
    json.dump(graph, outfile)

#get_cambridge_twitter_users()
users = json.loads(open(USERS_FILE).read())
#get_cambridge_twitter_friendships(users.keys())
friendships = json.loads(open(FRIENDSHIPS_FILE).read())
create_graph_from_users_and_friendships(users, friendships, "../data/cambridge_twitter_graph.json")
