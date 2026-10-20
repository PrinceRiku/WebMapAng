from airnet import load_us_network
from hubs import airport_degrees, nearest_airports, top_hubs


TOP_K = 10


def main():
    airports, _, edges, _ = load_us_network()
    if "TLH" not in airports:
        raise ValueError("TLH is not present in the loaded airport network")

    tlh_latitude = airports["TLH"][2]
    tlh_longitude = airports["TLH"][3]
    degrees = airport_degrees(edges)

    print(f"Top {TOP_K} airports by degree:")
    for rank, (iata, degree) in enumerate(top_hubs(edges, TOP_K), start=1):
        print(f"{rank:2}. {iata}: degree {degree}")

    nearest = nearest_airports(
        airports, edges, tlh_latitude, tlh_longitude, TOP_K
    )
    print(f"\n{TOP_K} nearest airports to TLH with at least one domestic route:")
    for rank, (iata, distance_km) in enumerate(nearest, start=1):
        print(f"{rank:2}. {iata}: {distance_km:.1f} km")

    direct_neighbor_codes = set()
    for source, destination in edges:
        if source == "TLH":
            direct_neighbor_codes.add(destination)
        elif destination == "TLH":
            direct_neighbor_codes.add(source)

    all_nearest = nearest_airports(
        airports, edges, tlh_latitude, tlh_longitude, len(airports)
    )
    direct_neighbors = [
        (iata, degrees[iata], distance_km)
        for iata, distance_km in all_nearest
        if iata in direct_neighbor_codes
    ]
    nearest_codes = [iata for iata, _ in nearest]
    nearest_direct = [iata for iata in nearest_codes if iata in direct_neighbor_codes]
    nearest_not_direct = [iata for iata in nearest_codes if iata not in direct_neighbor_codes]

    print("\nTLH direct neighbors (nearest first):")
    for iata, degree, distance_km in direct_neighbors:
        print(f"{iata}: degree {degree}, {distance_km:.1f} km from TLH")

    print("\nComparison:")
    print("Nearest airports that are also direct TLH neighbors:", nearest_direct or "none")
    print("Nearest airports without a direct TLH route:", nearest_not_direct or "none")
    print(
        "The geographically closest airports are not necessarily direct destinations. "
        "Airlines concentrate routes around hubs where passengers can connect, "
        "while direct routes depend on demand, operating cost, and aircraft capacity."
    )


if __name__ == "__main__":
    main()
