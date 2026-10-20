const DATA_FILES = [
  "airports.json",
  "edges.json",
  "lookup_codes.json",
  "hubs.json",
  "components.json",
  "summary.json",
];

const EARTH_RADIUS_KM = 6371;
const DEFAULT_CENTER = [39, -98];
const DEFAULT_ZOOM = 3.4;
const ROUTE_STYLE = { color: "#627b76", opacity: 0.16, weight: 1 };
const SELECTED_ROUTE_STYLE = { color: "#d86745", opacity: 0.88, weight: 2.4 };
const PATH_ROUTE_STYLE = { color: "#287d77", opacity: 0.78, weight: 2 };

let airports = [];
let edges = [];
let codes = [];
let hubs = [];
let components = [];
let summary = {};
let airportByCode = new Map();
let adjacency = new Map();
let map;
let markerByCode = new Map();
let routeByPair = new Map();
let currentHighlightedComponent = new Set();
let currentPath = null;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function pairKey(first, second) {
  return first < second ? `${first}|${second}` : `${second}|${first}`;
}

function binaryFind(code) {
  let low = 0;
  let high = codes.length - 1;
  let comparisons = 0;
  while (low <= high) {
    const middle = Math.floor((low + high) / 2);
    comparisons += 1;
    const candidate = codes[middle];
    if (candidate === code) return { index: middle, comparisons };
    if (code < candidate) high = middle - 1;
    else low = middle + 1;
  }
  return { index: -1, comparisons };
}

function haversineKm(first, second) {
  const radians = (degrees) => degrees * Math.PI / 180;
  const latitudeDelta = radians(second.latitude - first.latitude);
  const longitudeDelta = radians(second.longitude - first.longitude);
  const latitude1 = radians(first.latitude);
  const latitude2 = radians(second.latitude);
  const value = Math.sin(latitudeDelta / 2) ** 2
    + Math.cos(latitude1) * Math.cos(latitude2) * Math.sin(longitudeDelta / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(Math.min(1, value)));
}

function degreeColor(degree) {
  const maximum = Math.max(1, ...airports.map((airport) => airport.degree));
  const ratio = Math.min(1, degree / maximum);
  const stops = [[216, 103, 69], [215, 167, 53], [40, 125, 119]];
  const segment = ratio * 2;
  const left = Math.min(1, Math.floor(segment));
  const amount = segment - left;
  const first = stops[left];
  const second = stops[left + 1];
  const rgb = first.map((channel, index) => Math.round(channel + (second[index] - channel) * amount));
  return `rgb(${rgb.join(",")})`;
}

function renderLookup(code, { focusMap = true } = {}) {
  const normalized = code.trim().toUpperCase();
  const result = document.getElementById("lookup-result");
  const search = binaryFind(normalized);
  if (search.index < 0) {
    result.innerHTML = `<div class="not-found"><strong>${escapeHtml(normalized || "(blank)")}</strong> is not in this routed-airport network.</div><p class="search-count">Binary-search comparisons: <strong>${search.comparisons}</strong></p>`;
    return false;
  }

  const airport = airportByCode.get(normalized);
  const direct = [...(adjacency.get(normalized) || [])].sort();
  const nearest = airports
    .filter((candidate) => candidate.iata !== normalized)
    .map((candidate) => ({ ...candidate, distance: haversineKm(airport, candidate) }))
    .sort((first, second) => first.distance - second.distance || first.iata.localeCompare(second.iata))
    .slice(0, 5);
  const destinationsHtml = direct.length
    ? direct.map((destination) => `<span class="code-chip">${escapeHtml(destination)}</span>`).join("")
    : "<span class=\"empty-state\">No direct destinations</span>";
  const nearestHtml = nearest.map((candidate) => `
    <li><strong>${escapeHtml(candidate.iata)}</strong><span>${escapeHtml(candidate.city || candidate.name)}</span><span class="distance">${candidate.distance.toFixed(1)} km</span></li>
  `).join("");

  result.innerHTML = `
    <div class="result-top"><div><p class="result-code">${escapeHtml(airport.iata)}</p><p class="result-name">${escapeHtml(airport.name)}</p><p class="result-city">${escapeHtml(airport.city)}</p></div><span class="degree-badge">Degree ${airport.degree}</span></div>
    <div class="result-meta"><span>Direct destinations <strong>${direct.length}</strong></span><span>Binary comparisons <strong>${search.comparisons}</strong></span></div>
    <p class="lookup-section-title">Direct destinations</p><div class="destination-list">${destinationsHtml}</div>
    <p class="lookup-section-title">Five nearest routed airports</p><ol class="nearest-list">${nearestHtml}</ol>
  `;
  if (focusMap) selectAirportOnMap(normalized);
  return true;
}

function resetRouteStyles() {
  for (const layer of routeByPair.values()) layer.setStyle(ROUTE_STYLE);
}

function styleAirportMarkers() {
  for (const [code, marker] of markerByCode.entries()) {
    const airport = airportByCode.get(code);
    const selected = code === window.selectedAirportCode;
    const reached = currentPath?.reached.has(code) || false;
    const componentMember = currentHighlightedComponent.has(code);
    const stroke = selected ? "#d86745" : reached ? "#d86745" : componentMember ? "#d7a735" : "#fffefa";
    const weight = selected ? 3 : (reached || componentMember) ? 2.5 : 1;
    const fill = reached && currentPath?.path.has(code) ? "#173a36" : degreeColor(airport.degree);
    marker.setStyle({ color: stroke, weight, fillColor: fill, fillOpacity: 0.94 });
    marker.setRadius(3.2 + Math.sqrt(airport.degree) * 0.72 + (selected ? 1.5 : 0));
  }
}

function selectAirportOnMap(code) {
  window.selectedAirportCode = code;
  currentHighlightedComponent = new Set();
  currentPath = null;
  resetRouteStyles();
  const neighbors = adjacency.get(code) || new Set();
  for (const neighbor of neighbors) {
    const layer = routeByPair.get(pairKey(code, neighbor));
    if (layer) layer.setStyle(SELECTED_ROUTE_STYLE);
  }
  styleAirportMarkers();
  const marker = markerByCode.get(code);
  if (marker) marker.openPopup();
}

function highlightComponent(component) {
  currentHighlightedComponent = new Set(component.airports);
  currentPath = null;
  window.selectedAirportCode = null;
  resetRouteStyles();
  styleAirportMarkers();
  const members = component.airports.map((code) => markerByCode.get(code)).filter(Boolean);
  if (members.length) {
    const group = L.featureGroup(members);
    map.fitBounds(group.getBounds().pad(0.3), { maxZoom: 7 });
  }
}

function makeDegreeLegend() {
  const control = L.control({ position: "bottomright" });
  control.onAdd = () => {
    const element = L.DomUtil.create("div", "degree-legend");
    const maximum = Math.max(...airports.map((airport) => airport.degree));
    element.innerHTML = `<strong>Airport degree</strong><div class="legend-ramp"></div><div class="legend-labels"><span>1</span><span>${maximum}</span></div>`;
    return element;
  };
  control.addTo(map);
}

function addMapData() {
  map = L.map("network-map", { preferCanvas: true }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);
  L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
  }).addTo(map);

  const routePane = map.createPane("routes");
  routePane.style.zIndex = 350;
  const airportPane = map.createPane("airports");
  airportPane.style.zIndex = 450;

  for (const [source, destination] of edges) {
    const first = airportByCode.get(source);
    const second = airportByCode.get(destination);
    if (!first || !second) continue;
    const layer = L.polyline(
      [[first.latitude, first.longitude], [second.latitude, second.longitude]],
      { ...ROUTE_STYLE, pane: "routes", interactive: false },
    ).addTo(map);
    routeByPair.set(pairKey(source, destination), layer);
  }

  for (const airport of airports) {
    const marker = L.circleMarker([airport.latitude, airport.longitude], {
      pane: "airports",
      radius: 3.2 + Math.sqrt(airport.degree) * 0.72,
      color: "#fffefa",
      weight: 1,
      fillColor: degreeColor(airport.degree),
      fillOpacity: 0.94,
    }).addTo(map);
    marker.bindPopup(`<strong>${escapeHtml(airport.iata)}</strong> · ${escapeHtml(airport.name)}<br>${escapeHtml(airport.city)} · degree ${airport.degree}`);
    marker.on("click", () => {
      document.getElementById("lookup-code").value = airport.iata;
      renderLookup(airport.iata);
    });
    markerByCode.set(airport.iata, marker);
  }
  makeDegreeLegend();
  document.getElementById("fit-network").addEventListener("click", () => {
    const northAmerica = airports.filter((airport) => airport.latitude >= 15 && airport.longitude <= -60);
    const region = L.latLngBounds(northAmerica.map((airport) => [airport.latitude, airport.longitude]));
    map.fitBounds(region, { padding: [14, 14], maxZoom: 4.4 });
  });
}

function renderMetrics() {
  const metrics = [
    [summary.network_airport_count, "Routed airports"],
    [summary.unique_undirected_edge_count, "Unique edges"],
    [summary.component_count, "Components"],
    [summary.no_route_airport_count, "No domestic route"],
  ];
  document.getElementById("network-metrics").innerHTML = metrics.map(([value, label]) => `
    <div class="metric"><strong>${Number(value).toLocaleString()}</strong><span>${escapeHtml(label)}</span></div>
  `).join("");
  document.getElementById("map-count").textContent = `${airports.length.toLocaleString()} airports · ${edges.length.toLocaleString()} routes`;
  document.getElementById("snapshot-note").textContent = summary.data_year_note;
}

function renderHubChart() {
  const maximum = Math.max(...hubs.map((hub) => hub.degree));
  document.getElementById("hub-chart").innerHTML = hubs.map((hub) => `
    <button class="hub-row" type="button" data-code="${escapeHtml(hub.iata)}" aria-label="Select ${escapeHtml(hub.iata)}, degree ${hub.degree}">
      <span class="hub-code">${escapeHtml(hub.iata)}</span><span class="hub-track"><span class="hub-bar" style="display:block;width:${hub.degree / maximum * 100}%"></span></span><span class="hub-degree">${hub.degree}</span>
    </button>
  `).join("");
  document.querySelectorAll(".hub-row").forEach((button) => {
    button.addEventListener("click", () => {
      const code = button.dataset.code;
      document.getElementById("lookup-code").value = code;
      renderLookup(code);
      map.setView([airportByCode.get(code).latitude, airportByCode.get(code).longitude], Math.max(map.getZoom(), 5));
    });
  });
}

function renderComponents() {
  document.getElementById("component-list").innerHTML = components.map((component, index) => {
    const title = index === 0 ? "Largest network" : component.airports.slice(0, 3).join(" · ");
    return `<button class="component-button" type="button" data-component="${index}" aria-label="Highlight component ${index + 1}, ${component.size} airports"><span class="component-label">${escapeHtml(title)}</span><span class="component-size">${component.size}</span></button>`;
  }).join("");
  document.querySelectorAll(".component-button").forEach((button) => {
    button.addEventListener("click", () => highlightComponent(components[Number(button.dataset.component)]));
  });
  const note = document.createElement("p");
  note.className = "component-note";
  note.textContent = `Sizes: ${components.map((component) => component.size).join(", ")}`;
  document.getElementById("component-list").after(note);
}

function populateAirportMenus() {
  const options = codes.map((code) => {
    const airport = airportByCode.get(code);
    const label = airport.city || airport.name;
    return `<option value="${escapeHtml(code)}">${escapeHtml(code)} – ${escapeHtml(label)}</option>`;
  }).join("");
  document.getElementById("origin-code").innerHTML = options;
  document.getElementById("destination-code").innerHTML = options;
  document.getElementById("origin-code").value = "TLH";
  document.getElementById("destination-code").value = "SEA";
}

function runConnectionSearch(origin, destination) {
  const used = new Set();
  const untouched = new Set(codes);
  let current = new Set([origin]);
  untouched.delete(origin);
  const discovered = new Map([[origin, 0]]);
  const parent = new Map();
  let iterations = 0;
  let found = origin === destination;

  while (current.size > 0 && !found) {
    const next = new Set();
    for (const airport of current) {
      used.add(airport);
      for (const neighbor of adjacency.get(airport) || []) {
        if (untouched.has(neighbor)) {
          untouched.delete(neighbor);
          next.add(neighbor);
          discovered.set(neighbor, iterations + 1);
          parent.set(neighbor, airport);
        }
      }
    }
    current = next;
    iterations += 1;
    if (current.has(destination)) found = true;
  }

  const reached = new Set(discovered.keys());
  const path = new Set();
  if (found) {
    let cursor = destination;
    path.add(cursor);
    while (cursor !== origin) {
      cursor = parent.get(cursor);
      if (!cursor) break;
      path.add(cursor);
    }
  }
  return { found, iterations, reached, path, flights: discovered.get(destination), untouched: untouched.size };
}

function showConnectionResult(result, origin, destination) {
  const element = document.getElementById("connection-result");
  const answer = result.found ? "Path exists" : "No path";
  const flightLine = result.found
    ? `<span>Fewest flights: <strong>${result.flights}</strong> · Airports discovered: ${result.reached.size}</span>`
    : `<span>Search exhausted after ${result.iterations} iterations · Airports not reached: ${result.untouched}</span>`;
  element.innerHTML = `<div class="connection-answer ${result.found ? "" : "no-path"}"><strong>${answer}</strong><span>${escapeHtml(origin)} → ${escapeHtml(destination)} · ${result.iterations} iteration${result.iterations === 1 ? "" : "s"}</span>${flightLine}</div>`;

  currentPath = result;
  currentHighlightedComponent = new Set();
  window.selectedAirportCode = null;
  resetRouteStyles();
  for (const code of result.path) {
    const airport = airportByCode.get(code);
    if (!airport) continue;
    for (const neighbor of adjacency.get(code) || []) {
      if (!result.path.has(neighbor)) continue;
      const route = routeByPair.get(pairKey(code, neighbor));
      if (route) route.setStyle(PATH_ROUTE_STYLE);
    }
  }
  styleAirportMarkers();
  const reachedMarkers = [...result.reached].map((code) => markerByCode.get(code)).filter(Boolean);
  if (reachedMarkers.length) map.fitBounds(L.featureGroup(reachedMarkers).getBounds().pad(0.12), { maxZoom: 5 });
}

async function loadData() {
  const values = await Promise.all(DATA_FILES.map(async (filename) => {
    const response = await fetch(`data/${filename}`);
    if (!response.ok) throw new Error(`Could not load data/${filename} (${response.status})`);
    return response.json();
  }));
  [airports, edges, codes, hubs, components, summary] = values;
  airportByCode = new Map(airports.map((airport) => [airport.iata, airport]));
  adjacency = new Map(codes.map((code) => [code, new Set()]));
  for (const [source, destination] of edges) {
    adjacency.get(source)?.add(destination);
    adjacency.get(destination)?.add(source);
  }

  addMapData();
  renderMetrics();
  renderHubChart();
  renderComponents();
  populateAirportMenus();
  document.getElementById("load-status").textContent = "Network data ready";
  document.getElementById("lookup-code").value = "TLH";
  renderLookup("TLH");
  setTimeout(() => map.invalidateSize(), 0);
}

document.getElementById("lookup-form").addEventListener("submit", (event) => {
  event.preventDefault();
  renderLookup(document.getElementById("lookup-code").value);
});

document.getElementById("connection-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const origin = document.getElementById("origin-code").value;
  const destination = document.getElementById("destination-code").value;
  const result = runConnectionSearch(origin, destination);
  showConnectionResult(result, origin, destination);
});

loadData().catch((error) => {
  const status = document.getElementById("load-status");
  status.classList.add("error");
  status.textContent = `Network data failed to load: ${error.message}`;
  console.error(error);
});
