var svg;
var node_color;
var neighborhood_color;
var slider;
var width = 300, height = 300;
var graph;
var bbox = [[-71.16781724926273, 42.34361964310939], [-71.05788865715883, 42.41153795804243]];
var iterations_index = 0;
var neighborhood = "Mit";

window.onload = function() {
  // Set up map.
  var mapOptions = {
    width: 300, 
    height: 300,
    scale: 1,
    svgContainer: '#mapContainer',
    lookup: 'cambridge',
  }
  map = new D3Map(mapOptions); 
  queue()
    .defer(d3.json, 'data/CAMBRIDGE_NEIGHBORHOODS.geojson')
    .defer(d3.json, 'data/cambridge_twitter_graph.json')
    .await(setup);
}

function setup(error, geojson, twitter_graph) {
  map.loadGeoJSON(function() {
    svg = d3.select("#graphContainer").append("svg").attr("width", 700).attr("height", 600);
    node_color = d3.scale.linear().domain([0, .005]).range(['white', 'red']);
    neighborhood_color = d3.scale.linear().domain([0, 600]).range(['white', 'red']);
    slider = d3.select("#slider").attr("width", 1000);
    graph = twitter_graph;
    console.log(graph);
    path = d3.geo.path().projection(map.projection);
    handleProjectionFromBoundingBox(bbox, 300, 300);
    drawMap(geojson, path);
    drawGraph(graph.links);
    changeNeighborhood(neighborhood);
    updateGraph(iterations_index);
    drawSlider();
  });
}

function handleProjectionFromBoundingBox(bbox, width, height) {
  var feature = { 
      "type": "FeatureCollection",
          "features": [
              { "type": "Feature",
                "geometry": {"type": "Point", "coordinates": bbox[0]},
                "properties": {"prop0": "value0"}
              },
              { "type": "Feature",
                "geometry": {"type": "Point", "coordinates": bbox[1]},
                "properties": {"prop0": "value0"}
              },
          ]
      };
  map.projection.scale(1).translate([0, 0]);
  var b = d3.geo.path().projection(map.projection).bounds(feature),
      s = SCALE / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height),
      t = [(width - s * (b[1][0] + b[0][0])) / 2, (height - s * (b[1][1] + b[0][1])) / 2];
  map.projection.scale(s).translate(t);  
}

function drawMap(geojson, path) {
  var features = geojson.features;
  var neighborhoods = map.svg.selectAll('.neighborhood')
    .data(features)
    .enter().append('path')
    .attr('class', 'neighborhood')
    .attr('name', function(d) {
        d.neighborhood = d.properties.NAME;
        return d.properties.NAME;
    })
    .attr('d', path)
    .attr('fill', function(d) {
      //return neighborhood_color(graph["nodes"][d.neighborhood].length);
      return 'grey';
    })
    .attr('fill-opacity', .05)
    .on('mouseover', function(d) {
        neighborhoodMouseOver(d);
     })
     .on('mouseleave', function(d) {
        neighborhoodMouseOut(d);
     })
     .on('click', function(d) {
        neighborhoodMouseClick(d);
     });
}

function neighborhoodMouseOver(d) {
  if (neighborhood != d.neighborhood) {
    var selection = ".neighborhood[name='" + d.neighborhood.replace("'", "\\\'") + "']";
    map.svg.selectAll(selection).attr('stroke', 'black').attr('stroke-width', 2);
  }
}

function neighborhoodMouseOut(d) {
  if (neighborhood != d.neighborhood) {
    var selection = ".neighborhood[name='" + d.neighborhood.replace("'", "\\\'") + "']";
    map.svg.selectAll(selection).attr('stroke', 'black').attr('stroke-width', 0);
  }
}

function neighborhoodMouseClick(d) {
  changeNeighborhood(d.neighborhood);
}

function changeNeighborhood(n) {
  map.svg.selectAll(".neighborhood").attr('stroke', 'black').attr('stroke-width', 0);
  var selection = ".neighborhood[name='" + n.replace("'", "\\\'") + "']";
  map.svg.selectAll(selection).attr('stroke', 'black').attr('stroke-width', 4);
  neighborhood = n;
  updateInfo(neighborhood);

}
  

function drawGraph(links) {
    var nodes = {};
    links.forEach(function(link) {
        link.source = nodes[link.source] || (nodes[link.source] = {
            name: link.source
        });
        link.target = nodes[link.target] || (nodes[link.target] = {
            name: link.target
        });
        link.value = +link.value;
    });
    var force = d3.layout.force().nodes(d3.values(nodes)).links(links).size([ 700, 600 ]).linkDistance(5).charge(-100).on("tick", tick);
    svg.append("svg:defs").selectAll("marker").data([ "end" ]).enter().append("svg:marker").attr("id", String).attr("viewBox", "0 -5 10 10").attr("refX", 15).attr("refY", -1.5).attr("markerWidth", 6).attr("markerHeight", 6).attr("orient", "auto").append("svg:path").attr("d", "M0,-5L10,0L0,5");
    var path = svg.append("svg:g").selectAll("path").data(force.links()).enter().append("svg:path").attr("class", "link").attr("marker-end", "url(#end)");
    var node = svg.selectAll(".node").data(force.nodes()).enter().append("g").attr("class", "node");
    node.append("circle").attr("r", 5);
    force.start();
    for (var i = 0; i < 100; ++i) force.tick();
    force.stop();
    function tick() {
        path.attr("d", function(d) {
            var dx = d.target.x - d.source.x, dy = d.target.y - d.source.y, dr = Math.sqrt(dx * dx + dy * dy);
            return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
        });
        node.attr("transform", function(d) {
            return "translate(" + d.x + "," + d.y + ")";
        });
    }
};

function drawSlider() {
  iterationsdisplay = d3.select("body").selectAll("#iterations_display");
  start_button = d3.select("#start-button").on('click', startRun);
  iterations_slider = d3.select("body").select("#iterations_slider_container").append("input")
   .attr("type", "range")
   .attr("class", "slider")
   .attr("min", 0)
   .attr("max", Object.keys(graph.pagerank).length)
   .property("value", iterations_index)
   .attr("id", "iterations_slider")
 
  iterations_slider.on("change", function() {
    updateGraph(this.value);
  });
  d3.select("#reset-button").on('click', resetOnClick);
}

function updateInfo(neighborhood) {
  d3.selectAll('#neighborhoodDisplay').text(neighborhood);
  //d3.selectAll('#twitterUsersDisplay').text(graph["nodes"][neighborhood].length + " twitter users");
  //d3.selectAll('#twitterFriendshipsDisplay').text(graph["links"][neighborhood].length + " twitter users");
  d3.selectAll('#twitterUsersDisplay').text(graph["nodes"].length + " twitter users");
  d3.selectAll('#twitterFriendshipsDisplay').text(graph["links"].length + " twitter friendships");
}

function updateGraph(iterations_index) {
  iterations = Object.keys(graph.pagerank)[iterations_index];
  console.log(iterations);
  svg.selectAll("circle").transition().attr('fill', function(d) { return node_color(graph.pagerank[iterations][d.name])});
  d3.select("#iterations_slider").property("value", iterations_index);
  d3.select("body").selectAll("#iterations_display").transition().text(iterations);
}


function startRun() {
  if (iterations_index == Object.keys(graph.pagerank).length) {iterations_index = 0;}
  timer_stop = false;
  d3.select("#start-button").style("display", "none");
  pause_button = d3.select("#pause-button")
    .style("display", "inline")
    .on('click', pauseOnClick);
    runThrough();
}

function pauseOnClick() {
  timer_stop = true;
  clearInterval(clearVal);
  pause_button = d3.select("#pause-button");
  pause_button.style("display", "none");
  d3.select("#start-button").style("display", "inline");
}

function resetOnClick() {
  pauseOnClick();
  updateGraph(0);
}

function runThrough() {
  clearVal = setInterval(step, 500);
}

function step() {
  if (iterations_index < Object.keys(graph.pagerank).length) {
    iterations_index++;
    updateGraph(iterations_index);
    return timer_stop;
  } else {
    iterations_index = 0;
    updateGraph(iterations_index);
    resetOnClick();
    return true;
  }
}
