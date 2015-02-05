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
import math
import numpy as np
import utils

REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize?oauth_token="
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"

CONSUMER_KEY = "DLb9PnyxjhTwG0aykAFrR9Hfr"
CONSUMER_SECRET = "NbMTJTtjE0fVelwHxxpm1Hnj3t1M36d3Gajum16Q4SQhNaHKNX"

OAUTH_TOKEN = "431180881-U0Ywdjf8AZCdaPfZASAvHOtcKN3bRA0lHePxzE9e"
OAUTH_TOKEN_SECRET = "tk9BDjzVfTiGXbR3dgaV241Z24Hb0oAaDgdqpzxWQndmp"

CAMBRIDGE_POINTS_FILE = "../data/cambridge_points.json"

MAP_URL_NUM_RESULTS = "../data/map_url_num_results.json"
map_url_num_results = json.loads(open(MAP_URL_NUM_RESULTS).read())

queries = ["the", "i", "to", "a", "and", "is", "in", "it", "you", "of",
            "tinyurl.com", "for", "on", "my", "%27s", "that", "at", "with", "me", "do",
            "have", "just", "this", "be", "n%27t", "so", "are", "%27m", "not", "was",
            "but", "out", "up", "what", "now", "new", "from", "your", "like", "good",
            "no", "get", "all", "about", "we", "if", "time", "as", "day", "will"]
queries.append("patriots")
queries.append("%40")
queries.append("%23")
queries.append("montessori")
queries.append("%20") 

USERS_FILE = "../data/cambridge_twitter_users.json"
users = json.loads(open(USERS_FILE).read())

print "Loaded " + str(sum([len(users[key]) for key in users.keys()]) - len(users["cambridge"])) + " cambridge twitter users in " + str(len(users.keys()) - 1) + " neighborhoods"

FRIENDSHIPS_FILE = "../data/cambridge_twitter_friendships.json"
friendships = json.loads(open(FRIENDSHIPS_FILE).read())

MATRIX_FILE = "../data/cambridge_twitter_graph_matrix.json"
matrix = np.array(json.loads(open(MATRIX_FILE).read()))

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

def reset_users_file():
  cambridge_points = json.loads(open(CAMBRIDGE_POINTS_FILE).read())["points"]
  users = {}
  for neighborhood in cambridge_points.keys():
    users[neighborhood] = {}
  users["cambridge"] = {}
  with open(USERS_FILE, 'w') as outfile:
    json.dump(users, outfile)

def get_cambridge_twitter_users():
  if not OAUTH_TOKEN:
    token, secret = setup_oauth()
    print "OAUTH_TOKEN: " + token
    print "OAUTH_TOKEN_SECRET: " + secret
  else:
    oauth = get_oauth()
    cambridge_points = json.loads(open(CAMBRIDGE_POINTS_FILE).read())["points"]
    radius = json.loads(open(CAMBRIDGE_POINTS_FILE).read())["pitch"]
    print "Searching " + str(sum([len(cambridge_points[key]) for key in cambridge_points.keys()])) + " points for cambridge twitter users"
    for neighborhood in cambridge_points.keys():
      print neighborhood + ": Searching " + str(len(cambridge_points[neighborhood])) + " points for twitter users"
      for (i, point) in enumerate(cambridge_points[neighborhood]):
        for query in queries: 
          (new_users, new_map_url_num_results) = relax_circle(point, radius, query, oauth)
          if len(new_users.keys()) > 0:
            count = [0, 0]
            for user in new_users.keys():
              if user not in users["cambridge"].keys():
                users["cambridge"][user] = new_users[user]
                count[0] += 1
              if user not in users[neighborhood].keys():
                users[neighborhood][user] = new_users[user]
                count[1] += 1
            if count[0] > 0:
              print "---------------------Updating users file: " + str(len(users["cambridge"])) + " twitter users in cambridge---------------------"
            if count[1] > 0:
              print "---------------------Updating users file: " + str(len(users[neighborhood])) + " twitter users in " + neighborhood + "---------------------" 
            if count[1] > 0 or count[0] > 0:
              with open(USERS_FILE, 'w') as outfile:
                json.dump(users, outfile)
          if new_map_url_num_results:
            map_url_num_results.update(new_map_url_num_results)
            print "---------------------Updating map url num users file: " + str(len(map_url_num_results.keys())) + " urls searched---------------------"
            with open(MAP_URL_NUM_RESULTS, 'w') as outfile:
              json.dump(map_url_num_results, outfile)

"""
Performs tweet search on "query" over area defined by point and radius.  
If the query returns the max number of results, performs the same query
on 7 hexagonally packed circles inside the circle defined by point and radius
recursively until all queries return fewer than the maximum number of results.
Returns all users who had tweets matching query. 
"""
def relax_circle(point, radius, query, oauth):
  (new_users, new_map_url_num_results) = get_geocode_twitter_users(point, radius, query, oauth)
  if new_map_url_num_results and new_map_url_num_results.values()[0] > 99:
    circles = utils.get_hexagonally_packed_circles(point, radius)
    for circle in circles:
      (r_new_users, r_new_map_url_num_results) = relax_circle(circle[0], circle[1], query, oauth) 
      new_users.update(r_new_users)
      new_map_url_num_results.update(r_new_map_url_num_results)
  return (new_users, new_map_url_num_results)
    
"""
Searches the twitter API for tweets.  Searches each query at 
point "point" within radius "radius".  Returns a dictionary of the
users found, keyed by user_id.
"""
def get_geocode_twitter_users(point, radius, query, oauth):
  new_users = {}
  geocode = str(point[0]) + "," + str(point[1]) + "," + str(radius) + "mi"
  request_url = "https://api.twitter.com/1.1/search/tweets.json?q=" + query + "&geocode=" + geocode + "&count=100"
  if request_url in map_url_num_results.keys():
    return ({}, {})
  print "Trying request " + request_url
  r = requests.get(url=request_url, auth=oauth)

  # If we run out of requests, sleep for 30 minutes and try again
  while ('errors' in r.json().keys()):
    print "Found error in json response: \"" + r.json()["errors"][0]["message"]+ "\", sleeping for 15 minutes"
    time.sleep(15 * 60)
    r = requests.get(url=request_url, auth=oauth)

  num_results = len(r.json()["statuses"])

  print "Got " + str(num_results) + " results" 
  # Extract users from tweets
  for status in r.json()["statuses"]:
    user_id = str(status["user"]["id"])
    new_users[user_id] = status["user"]
  return (new_users, {request_url: num_results})

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
          print "Finding friendships for " + str(len(user_ids)) + " cambridge twitter users"
          print "Already have friendships for " + str(len(friendships.keys())) + " cambridge twitter users"
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

"""
def get_neighborhood_friendship_matrix(users, neighborhood, friendships):
  print "Getting friendship matrix for " + str(len(users[neighborhood].keys())) + " twitter users in " + neighborhood
  num_users = len(users[neighborhood].keys())
  matrix = np.zeros((num_users, num_users))
  for i, user_id in enumerate(users[neighborhood].keys()):
    if i % 10 == 0:
      print str(i) + "/" + str(num_users)
    if user_id not in friendships.keys():
      print "Can't find friendships for user " + user_id 
      continue
    neighborhood_friends = []
    for friend in [str(f) for f in friendships[user_id]]:
      if friend in users[neighborhood].keys():
        neighborhood_friends.append(friend)
    for friend in neighborhood_friends:
      print "Friendship between " + user_id + " and " + friend
      matrix[i][users.keys().index(friend)] = 1.0 / float(len(cambridge_friends))
  return matrix.tolist()

def get_cambridge_twitter_friendships(users, friendships):
    matrix = {}
    for neighborhood in users.keys():
        matrix["neighborhood"] = get_neighborhood_friendship_matrix(users, neighborhood, friendships) 
    with open(MATRIX_FILE, 'w') as outfile:
        json.dump(matrix.tolist(), outfile)
"""
      
def create_d3_data_from_friendship_matrix(users, matrix, graph_path):
  graph = {}
  nodes = []
  for user_id in users.keys():
    nodes.append({"group": 1, "id": str(user_id), "screen_name": users[user_id]["screen_name"], "name": users[user_id]["name"]})
  graph["nodes"] = nodes
  links = []
  for i, row in enumerate(matrix):
    for j, entry in enumerate(row):
      if entry > 0:
        links.append({"source": i, "target": j, "type":"friendship", "value":1})
        print "Found friendship between " + users.keys()[i] + " and " + users.keys()[j] 
  graph["links"] = links
  with open(graph_path, 'w') as outfile:
    json.dump(graph, outfile)


#get_cambridge_twitter_users()
get_cambridge_twitter_friendships(users["cambridge"].keys())
