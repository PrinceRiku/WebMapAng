import json
from pathlib import Path

from airnet import load_us_network
from find import selection_sort_codes
from hubs import airport_degrees, top_hubs
from path import connected_components


OUTPUT_DIR = Path(__file__).resolve().parent / "docs" / "data"


def export_web_data():
    airports, route_lines, edges, routed_airport_count = load_us_network()
    degrees = airport_degrees(edges)
    network_codes = set(degrees)
    sorted_codes = selection_sort_codes(list(network_codes))
    components = connected_components(edges)

    airport_records = []
    for code in sorted_codes:
        name, city, latitude, longitude = airports[code]
        airport_records.append(
            {
                "iata": code,
                "name": name,
                "city": city,
                "latitude": latitude,
                "longitude": longitude,
                "degree": degrees[code],
            }
        )

    airport_inventory_count = len(airports)
    no_route_codes = [code for code in airports if code not in network_codes]
    payloads = {
        "airports.json": airport_records,
        "edges.json": [list(edge) for edge in edges],
        "lookup_codes.json": sorted_codes,
        "hubs.json": [
            {"iata": code, "degree": degree}
            for code, degree in top_hubs(edges, 10)
        ],
        "components.json": [
            {"size": len(component), "airports": component}
            for component in components
        ],
        "summary.json": {
            "airport_inventory_count": airport_inventory_count,
            "network_airport_count": routed_airport_count,
            "no_route_airport_count": len(no_route_codes),
            "route_line_count": route_lines,
            "unique_undirected_edge_count": len(edges),
            "component_count": len(components),
            "component_sizes": [len(component) for component in components],
            "no_route_examples": no_route_codes[:10],
            "source": "OpenFlights airport and route data; airport records attributed to OurAirports",
            "route_snapshot_year": None,
            "data_year_note": "The supplied routes.dat file does not record a snapshot date.",
            "database_license": "Open Database License (ODbL) 1.0",
            "contents_license": "Database Contents License (DbCL) 1.0",
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, payload in payloads.items():
        output_path = OUTPUT_DIR / filename
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(payload, output_file, ensure_ascii=True, indent=2)
            output_file.write("\n")

    return payloads["summary.json"]


if __name__ == "__main__":
    summary = export_web_data()
    print(f"Exported web data to {OUTPUT_DIR}")
    print("Airport inventory:", summary["airport_inventory_count"])
    print("Routed network airports:", summary["network_airport_count"])
    print("Unique undirected edges:", summary["unique_undirected_edge_count"])
    print("Component sizes:", summary["component_sizes"])
