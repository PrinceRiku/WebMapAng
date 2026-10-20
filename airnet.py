import csv


US_COUNTRIES = {
    "united states",
    "united states minor outlying islands",
    "puerto rico",
    "guam",
    "us virgin islands",
    "virgin islands",
    "american samoa",
    "northern mariana islands",
}

EXCLUDED_AIRPORT_CODES = {"OEL", "TZR"}


def load_us_network(airports_file="data/airports.dat", routes_file="data/routes.dat"):
    """Load the U.S. airport network from the OpenFlights airport data files.

    This keeps airports in the United States and its territories, while
    preserving the original airport record data from the .dat files.

    Return the airports, domestic route-line count, unique undirected edges,
    and number of airports with at least one domestic route.
    """
    airports = {}
    airport_id_to_iata = {}

    with open(airports_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 8:
                continue

            airport_id = (row[0] or "").strip()
            country = (row[3] or "").strip()
            iata = (row[4] or "").strip().upper()

            country_key = country.strip().lower().replace(".", "").replace(",", "")
            if country_key not in US_COUNTRIES or iata in EXCLUDED_AIRPORT_CODES:
                continue

            if not airport_id:
                continue

            if not iata or len(iata) != 3 or not iata.isalpha():
                continue

            try:
                lat = float(row[6])
                lon = float(row[7])
            except (TypeError, ValueError):
                continue

            airport_id_to_iata[airport_id] = iata
            airports[iata] = (
                (row[1] or "").strip(),
                (row[2] or "").strip(),
                lat,
                lon,
            )

    edges = set()
    domestic_route_lines = 0
    domestic_airports = set()

    with open(routes_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 6:
                continue

            source_id = (row[3] or "").strip()
            dest_id = (row[5] or "").strip()

            if not source_id or not dest_id:
                continue

            source_iata = airport_id_to_iata.get(source_id)
            dest_iata = airport_id_to_iata.get(dest_id)

            if source_iata is None or dest_iata is None:
                continue

            domestic_route_lines += 1
            domestic_airports.update((source_iata, dest_iata))

            if source_iata == dest_iata:
                continue

            a, b = sorted((source_iata, dest_iata))
            edges.add((a, b))

    return (
        airports,
        domestic_route_lines,
        sorted(edges),
        len(domestic_airports),
    )

 