import csv
from collections import Counter

import plotly.graph_objects as go

from airnet import load_us_network

airports, domestic_route_lines, edges, airports_with_domestic_routes = load_us_network()

priority_edge = ("ATL", "TLH")
if priority_edge in edges:
    edges = [priority_edge] + [edge for edge in edges if edge != priority_edge]

with open("us_airports.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["iata", "name", "city", "latitude", "longitude"])
    for code, (name, city, latitude, longitude) in sorted(airports.items()):
        writer.writerow([code, name, city, latitude, longitude])

with open("us_edges.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["source", "destination"])
    writer.writerows(edges)

print("Number of U.S. airports:", len(airports))
print("Number of domestic route lines:", domestic_route_lines)
print("Number of unique undirected edges:", len(edges))
print("Number of airports with at least one domestic route:", airports_with_domestic_routes)
print("Saved airports to us_airports.csv")
print("Saved edges to us_edges.csv")

def map_region(airport):
    _, _, latitude, longitude = airport
    if 24 <= latitude <= 50 and -126 <= longitude <= -66:
        return "mainland"
    if latitude >= 50 and longitude <= -126:
        return "alaska"
    if 18 <= latitude <= 23 and -161 <= longitude <= -154:
        return "hawaii"
    return None

map_airports = {
    code: airport
    for code, airport in airports.items()
    if map_region(airport) is not None
}
map_edges = [
    edge for edge in edges if edge[0] in map_airports and edge[1] in map_airports
]
degrees = Counter(code for edge in map_edges for code in edge)
highlighted_edges = [edge for edge in map_edges if "TLH" in edge]
regular_edges = [edge for edge in map_edges if "TLH" not in edge]


def edge_coordinates(edge_list):
    longitudes = []
    latitudes = []
    for source, destination in edge_list:
        longitudes.extend([map_airports[source][3], map_airports[destination][3], None])
        latitudes.extend([map_airports[source][2], map_airports[destination][2], None])
    return longitudes, latitudes


figure = go.Figure()
edge_lon, edge_lat = edge_coordinates(regular_edges)
figure.add_trace(
    go.Scattergeo(
        lon=edge_lon,
        lat=edge_lat,
        mode="lines",
        line={"color": "rgba(58, 78, 83, 0.20)", "width": 0.7},
        hoverinfo="skip",
        name="Routes",
    )
)

edge_lon, edge_lat = edge_coordinates(highlighted_edges)
figure.add_trace(
    go.Scattergeo(
        lon=edge_lon,
        lat=edge_lat,
        mode="lines",
        line={"color": "#df5a3b", "width": 2.4},
        hoverinfo="skip",
        name="Direct routes from TLH",
    )
)

airport_codes = sorted(code for code in map_airports if degrees[code] > 0)
figure.add_trace(
    go.Scattergeo(
        lon=[map_airports[code][3] for code in airport_codes],
        lat=[map_airports[code][2] for code in airport_codes],
        mode="markers",
        customdata=[
            [code, map_airports[code][0], map_airports[code][1], degrees[code]]
            for code in airport_codes
        ],
        marker={
            "size": [4 + 1.7 * degrees[code] ** 0.5 for code in airport_codes],
            "color": [degrees[code] for code in airport_codes],
            "colorscale": "Viridis",
            "showscale": True,
            "colorbar": {"title": "Route degree", "thickness": 12},
            "line": {"color": "white", "width": 0.5},
            "opacity": 0.88,
        },
        hovertemplate=(
            "<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
            "%{customdata[2]}<br>Degree: %{customdata[3]}<extra></extra>"
        ),
        name="Airports",
    )
)

zero_route_codes = sorted(code for code in map_airports if degrees[code] == 0)
figure.add_trace(
    go.Scattergeo(
        lon=[map_airports[code][3] for code in zero_route_codes],
        lat=[map_airports[code][2] for code in zero_route_codes],
        mode="markers",
        customdata=[
            [code, map_airports[code][0], map_airports[code][1], degrees[code]]
            for code in zero_route_codes
        ],
        marker={
            "size": 5,
            "color": "#aab5b5",
            "line": {"color": "white", "width": 0.5},
            "opacity": 0.72,
        },
        hovertemplate=(
            "<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
            "%{customdata[2]}<br>Degree: %{customdata[3]}<extra></extra>"
        ),
        name="Airports with 0 routes (click to hide)",
    )
)

hub_codes = [
    code
    for code, _ in sorted(degrees.items(), key=lambda item: (-item[1], item[0]))[:12]
    if code != "TLH"
]
figure.add_trace(
    go.Scattergeo(
        lon=[map_airports[code][3] for code in hub_codes],
        lat=[map_airports[code][2] for code in hub_codes],
        text=hub_codes,
        mode="text",
        textfont={"size": 10, "color": "#172c32"},
        textposition="top center",
        hoverinfo="skip",
        showlegend=False,
        name="Largest hubs",
    )
)

if "TLH" in map_airports:
    figure.add_trace(
        go.Scattergeo(
            lon=[map_airports["TLH"][3]],
            lat=[map_airports["TLH"][2]],
            mode="markers+text",
            text=["TLH"],
            textposition="bottom right",
            textfont={"size": 11, "color": "#a83d28"},
            marker={
                "size": 12,
                "color": "#df5a3b",
                "symbol": "diamond",
                "line": {"color": "white", "width": 1.2},
            },
            hovertemplate="<b>TLH</b><br>Tallahassee International Airport<extra></extra>",
            name="TLH",
        )
    )

figure.update_layout(
    title={
        "text": "U.S. Airport Network | Mainland, Alaska & Hawaii",
        "x": 0.04,
        "xanchor": "left",
    },
    geo={
        "scope": "usa",
        "projection": {"type": "albers usa"},
        "showland": True,
        "landcolor": "#f1f0e8",
        "showocean": True,
        "oceancolor": "#e5f0f2",
        "showlakes": True,
        "lakecolor": "#e5f0f2",
        "showcoastlines": True,
        "coastlinecolor": "#72939a",
        "showcountries": True,
        "countrycolor": "#8ca0a0",
        "showsubunits": True,
        "subunitcolor": "#a9b1a8",
        "subunitwidth": 0.7,
        "showframe": False,
        "bgcolor": "#e5f0f2",
    },
    paper_bgcolor="#faf9f4",
    plot_bgcolor="#faf9f4",
    font={"family": "Arial, sans-serif", "color": "#24363a"},
    legend={"orientation": "h", "y": 0.04, "x": 0.04},
    margin={"l": 10, "r": 20, "t": 70, "b": 85},
    annotations=[
        {
            "text": (
                "Alaska and Hawaii are shown in the Albers USA projection. "
                "Territories are omitted from this map view, but remain in the airport/edge counts and CSV exports."
            ),
            "xref": "paper",
            "yref": "paper",
            "x": 0.02,
            "y": -0.08,
            "xanchor": "left",
            "showarrow": False,
            "font": {"size": 11, "color": "#52676a"},
        }
    ],
)

figure.write_html("us_air_network_map.html", include_plotlyjs=True)
print("Saved interactive map to us_air_network_map.html")
print("Airports shown on map:", len(map_airports))
print("Edges shown on map:", len(map_edges))