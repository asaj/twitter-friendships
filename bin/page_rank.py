import math
import json
import numpy as np
import random
import networkx as nx
import page_rank_impl as pr

USERS_FILE = "../data/cambridge_twitter_users.json"
users = json.loads(open(USERS_FILE).read())
print "Loaded " + str(len(users.keys())) + " cambridge twitter users"

FRIENDSHIPS_FILE = "../data/cambridge_twitter_friendships.json"
friendships = json.loads(open(FRIENDSHIPS_FILE).read())

MATRIX_FILE = "../data/cambridge_twitter_graph_matrix.json"
matrix = json.loads(open(MATRIX_FILE).read())

D3_DATA_FILE = "../data/cambridge_twitter_graph.json"
graph = json.loads(open(D3_DATA_FILE).read())

def get_friendship_matrix(users, friendships):
  print "Getting friendship matrix for " + str(len(users.keys())) + " twitter users"
  num_users = len(users.keys())
  matrix = np.zeros((num_users, num_users))
  for i, user_id in enumerate(users.keys()):
    if i % 10 == 0:
      print str(i) + "/" + str(num_users)
    if user_id not in friendships.keys():
      print "Can't find friendships for user " + user_id 
      continue
    cambridge_friends = []
    for friend in [str(f) for f in friendships[user_id]]:
      if friend in users.keys():
        cambridge_friends.append(friend)
    for friend in cambridge_friends:
      print "Friendship between " + user_id + " and " + friend
      matrix[i][users.keys().index(friend)] = 1.0 / float(len(cambridge_friends))
  with open(MATRIX_FILE, 'w') as outfile:
    json.dump(matrix.tolist(), outfile)
  return matrix
      
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

def run_pagerank_from_friendship_matrix(matrix, iterations, graph, graph_path):
  print "Getting friendship matrix for " + str(len(users.keys())) + " twitter users"
  nodes = [i for i in range(len(matrix))]
  starting_nodes = []
  for n in nodes:
    if random.random() < .01:
      starting_nodes.append(n)
  nstart = {}
  for n in nodes:
    if n in starting_nodes:
      nstart[n] = 1.0 / float(len(starting_nodes))
    else:
      nstart[n] = 0
  G = nx.DiGraph()
  G.add_nodes_from(nodes)
  for i, row in enumerate(matrix):
    for j, value in enumerate(matrix):
      if matrix[i][j] > 0:
        G.add_edge(i, j)
        #print "Edge between " + str(i) + " and " + str(j)
  map_iterations_pagerank= {}
  for i in iterations:
    map_iterations_pagerank[i] = pr.pagerank(G, max_iter=i, nstart=nstart, tol=0.0)
    print map_iterations_pagerank[i][1]
  graph["pagerank"] = map_iterations_pagerank
  with open(graph_path, 'w') as outfile:
    json.dump(graph, outfile)
  return map_iterations_pagerank



#matrix = get_friendship_matrix(users, friendships)
#create_d3_data_from_friendship_matrix(users, matrix, "../data/cambridge_twitter_graph.json")

iterations = [i for i in range(10)]
run_pagerank_from_friendship_matrix(matrix, iterations, graph, "../data/cambridge_twitter_graph.json")
