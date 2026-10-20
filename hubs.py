import math


def airport_degrees(edges):
    """Return each airport's degree in the undirected edge list."""
    degrees = {}
    for source, destination in edges:
        if source == destination:
            degrees[source] = degrees.get(source, 0) + 2
            continue
        degrees[source] = degrees.get(source, 0) + 1
        degrees[destination] = degrees.get(destination, 0) + 1
    return degrees


def _selection_sort(records, comes_before):
    """Sort records in place using selection sort and return them."""
    for index in range(len(records)):
        best_index = index
        for candidate_index in range(index + 1, len(records)):
            if comes_before(records[candidate_index], records[best_index]):
                best_index = candidate_index
        records[index], records[best_index] = records[best_index], records[index]
    return records


def top_hubs(edges, k):
    """Return up to k (IATA, degree) pairs, highest degree first."""
    if k <= 0:
        return []

    hubs = list(airport_degrees(edges).items())
    _selection_sort(
        hubs,
        lambda left, right: left[1] > right[1]
        or (left[1] == right[1] and left[0] < right[0]),
    )
    return hubs[:k]


def _haversine_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))

    latitude_delta = lat2 - lat1
    longitude_delta = lon2 - lon1
    haversine_value = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(longitude_delta / 2) ** 2
    )
    central_angle = 2 * math.asin(math.sqrt(min(1.0, haversine_value)))
    return earth_radius_km * central_angle


def nearest_airports(airports, edges, lat, lon, k):
    """Return up to k routed airports nearest to the supplied coordinates."""
    if k <= 0:
        return []

    routed_airports = airport_degrees(edges)
    nearest = []
    for iata in routed_airports:
        if iata not in airports:
            continue
        if airports[iata][2] == lat and airports[iata][3] == lon:
            continue
        distance_km = _haversine_km(lat, lon, airports[iata][2], airports[iata][3])
        nearest.append((iata, distance_km))

    _selection_sort(
        nearest,
        lambda left, right: left[1] < right[1]
        or (left[1] == right[1] and left[0] < right[0]),
    )
    return nearest[:k]
