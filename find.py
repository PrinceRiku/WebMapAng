def build_codes(edges):
    """Return routed airport codes in first-appearance edge order."""
    codes = []
    seen = set()
    for source, destination in edges:
        if source not in seen:
            seen.add(source)
            codes.append(source)
        if destination not in seen:
            seen.add(destination)
            codes.append(destination)
    return codes


def selection_sort_codes(codes):
    """Return a copy of codes sorted alphabetically using selection sort."""
    sorted_codes = list(codes)
    for index in range(len(sorted_codes)):
        smallest_index = index
        for candidate_index in range(index + 1, len(sorted_codes)):
            if sorted_codes[candidate_index] < sorted_codes[smallest_index]:
                smallest_index = candidate_index
        sorted_codes[index], sorted_codes[smallest_index] = (
            sorted_codes[smallest_index],
            sorted_codes[index],
        )
    return sorted_codes


def sequential_find(codes, code):
    """Scan codes from the start; count one comparison for each code checked."""
    comparisons = 0
    for index, candidate in enumerate(codes):
        comparisons += 1
        if candidate == code:
            return index, comparisons
    return -1, comparisons


def find_airport(sorted_codes, code):
    """Binary-search sorted_codes; count one comparison for each midpoint probe."""
    low = 0
    high = len(sorted_codes) - 1
    comparisons = 0

    while low <= high:
        mid = (low + high) // 2
        comparisons += 1
        candidate = sorted_codes[mid]
        if candidate == code:
            return mid, comparisons
        if code < candidate:
            high = mid - 1
        else:
            low = mid + 1

    return -1, comparisons
