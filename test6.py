from collections import Counter

import plotly.graph_objects as go

from airnet import load_us_network
from path import connected_components, discovery_layers, path_exists


PATH_TESTS = (("TLH", "SEA"), ("TLH", "AKB"), ("DUT", "AKB"), ("PSM", "SEA"))
CHART_FILE = "tlh_flights_by_connection.html"


def _airport_label(code, airports):
    name, city, _, _ = airports[code]
    return f"{code}: {name} ({city})"


def report_path_tests(edges, airports, components):
    print("Path existence tests:")
    results = {}
    for origin, destination in PATH_TESTS:
        verbose = (origin, destination) == ("DUT", "AKB")
        found, iterations = path_exists(edges, origin, destination, verbose=verbose)
        results[(origin, destination)] = found
        print(
            f"{origin} to {destination}: path_exists={found}, "
            f"iterations={iterations}"
        )

        if (origin, destination) == ("TLH", "AKB") and not found:
            graph_airports = {code for edge in edges for code in edge}
            tlh_component = next(
                (component for component in components if "TLH" in component), []
            )
            untouched_at_stop = len(graph_airports) - len(tlh_component)
            print(
                "TLH-to-AKB takes several iterations because each iteration "
                "expands the search by one connection layer. The algorithm can "
                "answer no only after exhausting TLH's entire connected component. "
                f"At that point untouched has {untouched_at_stop} airports: these "
                "were never discovered from TLH and belong to other components."
            )

    return results


def report_components(edges, airports, components):
    print(f"\nConnected components: {len(components)}")
    print("Component sizes (largest first):", [len(component) for component in components])
    print("\nAirports in every component other than the largest:")

    for component_number, component in enumerate(components[1:], start=2):
        print(f"Component {component_number} (size {len(component)}):")
        for code in component:
            if code in airports:
                print(f"  {_airport_label(code, airports)}")
            else:
                print(f"  {code}: missing from airport records")

    print(
        "The AKB/DUT/IKO/KQA component is a group of Aleutian Islands airports. "
        "The BFI/CLM/ESD/FRD component is in the Seattle and Puget Sound area; "
        "BFI is Boeing Field, not Seattle-Tacoma International. Their isolation "
        "from the largest component likely reflects the limited route records "
        "for these smaller airports, rather than physical separation alone."
    )

    print("\nChecking components against path_exists:")
    checks = 0
    consistent = True
    for component in components:
        if not component:
            continue
        origin = component[0]
        for destination in component:
            found, _ = path_exists(edges, origin, destination)
            checks += 1
            if not found:
                consistent = False
                print(f"ERROR: {origin} and {destination} share a component but no path was found")

    for first_index, first_component in enumerate(components):
        for second_component in components[first_index + 1:]:
            if not first_component or not second_component:
                continue
            found, _ = path_exists(edges, first_component[0], second_component[0])
            checks += 1
            if found:
                consistent = False
                print(
                    f"ERROR: {first_component[0]} and {second_component[0]} "
                    "are in different components but a path was found"
                )

    print(f"Checked {checks} representative path pairs; consistent={consistent}")
    print(
        "Small components can reflect genuinely isolated regional or island "
        "networks, but also gaps in the route data. This graph is filtered to "
        "domestic routes between the selected U.S. airports, so both geography "
        "and the dataset/filtering can contribute to disconnection."
    )


def report_airports_without_routes(airports, edges):
    routed_airports = {code for edge in edges for code in edge}
    no_route_airports = [code for code in airports if code not in routed_airports]
    no_route_airports.sort()

    print(f"\nU.S. airports with no domestic route: {len(no_route_airports)}")
    print("Examples:")
    for code in no_route_airports[:10]:
        print(f"  {_airport_label(code, airports)}")
    print(
        "Possible reasons include airports present in the airport inventory but "
        "absent from this route snapshot, small/private or military fields, "
        "closed facilities, or routes omitted by the data source/filter."
    )
    return no_route_airports


def report_tlh_flight_layers(edges, airports, layers):
    layer_counts = Counter(layers.values())
    maximum_iteration = max(layer_counts, default=0)

    print("\nAirports first discovered from TLH by number of flights:")
    print(f"{'Flights':>8} {'Airports discovered':>20}")
    print("-" * 29)
    for iteration in range(1, maximum_iteration + 1):
        print(f"{iteration:8} {layer_counts[iteration]:20}")

    figure = go.Figure(
        data=[
            go.Bar(
                x=list(range(1, maximum_iteration + 1)),
                y=[layer_counts[iteration] for iteration in range(1, maximum_iteration + 1)],
                marker_color="#287d77",
                text=[layer_counts[iteration] for iteration in range(1, maximum_iteration + 1)],
                textposition="outside",
            )
        ]
    )
    figure.update_layout(
        title="Airports Reached from TLH by Number of Flights",
        xaxis_title="Flights from TLH (connection iteration)",
        yaxis_title="Airports first discovered",
        template="plotly_white",
        margin={"l": 60, "r": 30, "t": 70, "b": 60},
    )
    figure.write_html(CHART_FILE, include_plotlyjs=True)
    print(f"Saved flight-layer bar chart to {CHART_FILE}")

    if maximum_iteration:
        farthest_airports = [
            code for code, iteration in layers.items() if iteration == maximum_iteration
        ]
        print(f"\nMost flights from TLH: {maximum_iteration}")
        for code in sorted(farthest_airports):
            if code in airports:
                print(f"  {_airport_label(code, airports)}")
            else:
                print(f"  {code}: missing from airport records")
        print(
            "These airports are farthest in route-network steps, not necessarily "
            "geographic distance. Sparse regional connections and hub-and-spoke "
            "routing can make nearby places require several transfers."
        )

    graph_airports = {code for edge in edges for code in edge}
    unreachable = graph_airports - set(layers)
    print(f"Airports in other components, unreachable from TLH: {len(unreachable)}")


def main():
    airports, _, edges, _ = load_us_network()
    components = connected_components(edges)

    report_path_tests(edges, airports, components)
    report_components(edges, airports, components)
    report_airports_without_routes(airports, edges)

    layers = discovery_layers(edges, "TLH")
    report_tlh_flight_layers(edges, airports, layers)


if __name__ == "__main__":
    main()
