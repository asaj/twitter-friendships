var svg;
var clearVal;
var node_color;
var neighborhood_color;
var slider;
var width = 300, height = 300;
var graph;
var bbox = [[-71.16781724926273, 42.34361964310939], [-71.05788865715883, 42.41153795804243]];
var iterations_index = 0;
var neighborhood = "Mit";
var force_nodes = {};

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
    neighborhood_color = d3.scale.linear().domain([0, 2000]).range(['white', 'red']);
    slider = d3.select("#slider").attr("width", 1000);
    graph = twitter_graph;
    path = d3.geo.path().projection(map.projection);
    handleProjectionFromBoundingBox(bbox, 300, 300);
    drawMap(geojson, path);
    initializeLinks(graph);
    changeNeighborhood(neighborhood);
    drawSlider();
  });
}
function initializeLinks(graph) {
  Object.keys(graph).forEach(function(neighborhood) {
    var nodes = {};
    graph[neighborhood].links.forEach(function(link) {
        link.source = nodes[link.source] || (nodes[link.source] = {
            name: link.source, 
            screen_name: graph[neighborhood].nodes[link.source_id].screen_name
        });
        link.target = nodes[link.target] || (nodes[link.target] = {
            name: link.target,
            screen_name: graph[neighborhood].nodes[link.target_id].screen_name
        });
        link.value = +link.value;
    });
    force_nodes[neighborhood] = nodes;
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
      return neighborhood_color(Object.keys(graph[d.neighborhood].nodes).length);
    })
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
  d3.selectAll(".node").remove();
  d3.selectAll(".link").remove();
  drawGraph(graph[neighborhood].links, force_nodes[neighborhood]);
  iterations_index = 0;
  updateGraph(iterations_index);
  resetOnClick();
  d3.selectAll('.node').call(tip);
}
var tip = d3.tip()
    .attr('class', 'd3-tip')
    .offset([-10, 0])
    .html(function(d) {
        d.text = d.screen_name;
        return "<div class='tip' style='color:#fff; max-width: 200px; font-weight: normal; text-align: center;'>" + d.text + "</div>";
    });
  
function drawGraph(links, nodes) {
    var force = d3.layout.force().nodes(d3.values(nodes)).links(links).size([ 700, 600 ]).linkDistance(50).charge(-50).on("tick", tick);
    svg.append("svg:defs").selectAll("marker").data([ "end" ]).enter().append("svg:marker").attr("id", String).attr("viewBox", "0 -5 10 10").attr("refX", 15).attr("refY", -1.5).attr("markerWidth", 6).attr("markerHeight", 6).attr("orient", "auto").append("svg:path").attr("d", "M0,-5L10,0L0,5");
    var path = svg.append("svg:g").selectAll("path").data(force.links()).enter().append("svg:path").attr("class", "link").attr("marker-end", "url(#end)");
    var node = svg.selectAll(".node").data(force.nodes()).enter().append("g").attr("class", "node").on('mouseover', tip.show).on('mouseout', tip.hide);
    node.append("circle").attr("r", 5).attr("fill", "white");
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
   .attr("max", Object.keys(graph[neighborhood].pagerank).length - 1)
   .property("value", iterations_index)
   .attr("id", "iterations_slider")
 
  iterations_slider.on("change", function() {
    updateGraph(this.value);
  });
  d3.select("#reset-button").on('click', resetOnClick);
}

function updateInfo(neighborhood) {
  d3.selectAll('#neighborhoodDisplay').text(neighborhood);
  d3.selectAll('#twitterUsersDisplay').text(Object.keys(graph[neighborhood].nodes).length + " twitter users");
  d3.selectAll('#twitterFriendshipsDisplay').text(graph[neighborhood].links.length + " friendships");
}

function updateGraph(iterations_index) {
  node_color = d3.scale.linear().domain([0, 20.0 / (Object.keys(graph[neighborhood].nodes).length)]).range(['white', 'red']);
  iterations = Object.keys(graph[neighborhood].pagerank)[iterations_index];
  svg.selectAll("circle").transition().attr('fill', function(d) { return node_color(graph[neighborhood].pagerank[iterations][d.name])});
  d3.select("#iterations_slider").property("value", iterations_index);
  d3.select("body").selectAll("#iterations_display").transition().text(iterations);
  //d3.selectAll('.link').transition().style('stroke', function(d) { return node_color(graph[neighborhood].pagerank[iterations][d.source.name]);}); 
}


function startRun() {
  if (iterations_index == Object.keys(graph[neighborhood].pagerank).length) {iterations_index = 0;}
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
  iterations_index = 0;
  pauseOnClick();
  updateGraph(0);
}

function runThrough() {
  clearVal = setInterval(step, 100);
}

function step() {
  if (iterations_index < Object.keys(graph[neighborhood].pagerank).length - 1) {
    iterations_index++;
    updateGraph(iterations_index);
    return timer_stop;
  } else {
    //iterations_index = 0;
    //updateGraph(iterations_index);
    //resetOnClick();
    pauseOnClick();
    return true;
  }
}
