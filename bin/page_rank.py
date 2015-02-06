import math
import json
import numpy as np
import random
import networkx as nx
import page_rank_impl as pr

USERS_FILE = "../data/cambridge_twitter_users.json"
users = json.loads(open(USERS_FILE).read())
print "Loaded " + str(len(users["cambridge"].keys())) + " cambridge twitter users"

FRIENDSHIPS_FILE = "../data/cambridge_twitter_friendships.json"
friendships = json.loads(open(FRIENDSHIPS_FILE).read())

MATRIX_FILE = "../data/cambridge_twitter_graph_matrix.json"
matrix = json.loads(open(MATRIX_FILE).read())

D3_DATA_FILE = "../data/cambridge_twitter_graph.json"
graph = json.loads(open(D3_DATA_FILE).read())

def get_neighborhood_friendship_matrix(users, neighborhood, friendships):
  print "Getting friendship matrix for " + str(len(users[neighborhood].keys())) + " twitter users in " + neighborhood
  num_users = len(users[neighborhood].keys())
  matrix = np.zeros((num_users, num_users))

  num_no_friendships = 0
  for i, user_id in enumerate(users[neighborhood].keys()):
    if user_id not in friendships.keys():
      num_no_friendships += 1 
      continue
    neighborhood_friends = []
    for friend in [str(f) for f in friendships[user_id]]:
      if friend in users[neighborhood].keys():
        neighborhood_friends.append(friend)
    for friend in neighborhood_friends:
      matrix[i][users[neighborhood].keys().index(friend)] = 1.0 / float(len(neighborhood_friends))
  print "Couldn't find friendships for " + str(num_no_friendships) + "/" + str(len(users[neighborhood].keys())) + " twitter users in " + neighborhood
  return matrix.tolist()

def get_cambridge_friendship_matrix(users, friendships):
    matrix = {}
    for neighborhood in users.keys():
        if neighborhood == "cambridge":
          continue
        matrix[neighborhood] = get_neighborhood_friendship_matrix(users, neighborhood, friendships) 
    with open(MATRIX_FILE, 'w') as outfile:
        json.dump(matrix, outfile)
    return matrix

def run_pagerank_from_friendship_matrix(matrix,  iterations):
  nodes = [i for i in range(len(matrix))]
  """
  starting_nodes = []
  for n in nodes:
    if random.random() < .05:
      starting_nodes.append(n)
  nstart = {}
  for n in nodes:
    if n in starting_nodes:
      nstart[n] = 1.0 / float(len(starting_nodes))
    else:
      nstart[n] = 0
  """
  G = nx.DiGraph()
  G.add_nodes_from(nodes)
  for i, row in enumerate(matrix):
    for j, value in enumerate(matrix):
      if matrix[i][j] > 0:
        G.add_edge(i, j)
        #print "Edge between " + str(i) + " and " + str(j)
  map_iterations_pagerank= {}
  for i in iterations:
    map_iterations_pagerank[i] = pr.pagerank(G, max_iter=i, tol=0.0)
  return map_iterations_pagerank
      
def create_d3_data_from_friendship_matrix(users, matrix, iterations, graph_path):
  graph = {}
  for neighborhood in users.keys():
    if neighborhood == "cambridge":
      continue
    graph[neighborhood] = {}
    nodes = {}
    for user_id in users[neighborhood].keys():
      nodes[user_id] = {"group": 1, "id": str(user_id), "screen_name": users[neighborhood][user_id]["screen_name"], "text":users[neighborhood][user_id]["screen_name"], "name": users[neighborhood][user_id]["name"]}
    graph[neighborhood]["nodes"] = nodes
    #graph[neighborhood]["nodes"] = users[neighborhood][user_id]
    links = []
    for i, row in enumerate(matrix[neighborhood]):
      for j, entry in enumerate(row):
        if entry > 0:
          links.append({"source": i, "source_id":users[neighborhood].keys()[i], "target": j, "target_id":users[neighborhood].keys()[j], "type":"friendship", "value":1})
          #print "Found friendship between " + users[neighborhood].keys()[i] + " and " + users[neighborhood].keys()[j] 
    graph[neighborhood]["links"] = links
    print "Running pagerank on matrix for " + neighborhood
    graph[neighborhood]["pagerank"] = run_pagerank_from_friendship_matrix(matrix[neighborhood], iterations) 
  with open(graph_path, 'w') as outfile:
    json.dump(graph, outfile)

#matrix = get_cambridge_friendship_matrix(users, friendships)
iterations = [i for i in range(17)]
create_d3_data_from_friendship_matrix(users, matrix, iterations, "../data/cambridge_twitter_graph.json")
