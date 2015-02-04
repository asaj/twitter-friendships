import json
import random

NUM_NODES = 100
CONNECTION_PROBABILITY = .02
NUM_BOOKMARKS = 10
GRAPH_FILE = "../data/dummy_graph.json"
OPACITY_FILE = "../data/dummy_opacity.json"

r = {}

nodes = [{"name": str(x), "group":1} for x in range(NUM_NODES)]
links = []
bookmarks = []

for node in nodes:
  if (random.random() < float(NUM_BOOKMARKS) / float(NUM_NODES)):
    bookmarks.append(node)

for node in nodes:
  for node2 in nodes:
    if node != node2 and random.random() < CONNECTION_PROBABILITY:
      links.append({"source": int(node["name"]), "target":int(node2["name"]), "type":"friendship", "value":1})

r["bookmarks"] = bookmarks
r["nodes"] = nodes
r["links"] = links

with open(GRAPH_FILE, 'w') as outfile:
  json.dump(r, outfile)

with open(OPACITY_FILE, 'w') as outfile:
  json.dump(r, outfile)
