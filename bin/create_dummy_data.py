import json
import random


with open(GRAPH_FILE, 'w') as outfile:
  json.dump(r, outfile)

with open(OPACITY_FILE, 'w') as outfile:
  json.dump(r, outfile)
