import math
import random
import string
import time

from airnet import load_us_network
from find import build_codes, find_airport, selection_sort_codes, sequential_find


QUERY_COUNT_PER_TYPE = 5000
RANDOM_SEED = 56789
TRACE_CODES = ("ATL", "TLH", "ZZZ")


def trace_binary_search(sorted_codes, code):
    low = 0
    high = len(sorted_codes) - 1
    comparisons = 0

    print(f"\nBinary-search trace for {code}:")
    while low <= high:
        mid = (low + high) // 2
        candidate = sorted_codes[mid]
        comparisons += 1
        print(f"low={low:3} high={high:3} mid={mid:3} code_at_mid={candidate}")
        if candidate == code:
            return mid, comparisons
        if code < candidate:
            high = mid - 1
        else:
            low = mid + 1

    return -1, comparisons


def make_queries(codes):
    generator = random.Random(RANDOM_SEED)
    valid_queries = [
        generator.choice(codes) for _ in range(QUERY_COUNT_PER_TYPE)
    ]

    code_set = set(codes)
    invalid_queries = []
    while len(invalid_queries) < QUERY_COUNT_PER_TYPE:
        candidate = "".join(
            generator.choice(string.ascii_uppercase) for _ in range(3)
        )
        if candidate not in code_set:
            invalid_queries.append(candidate)

    return valid_queries, invalid_queries


def measure_search(search_function, search_codes, queries):
    comparison_counts = []
    start_time = time.perf_counter()
    for query in queries:
        _, comparisons = search_function(search_codes, query)
        comparison_counts.append(comparisons)
    elapsed_seconds = time.perf_counter() - start_time
    return elapsed_seconds, comparison_counts


def print_results_table(codes, sorted_codes, valid_queries, invalid_queries):
    print("\nLookup benchmark (10,000 total queries):")
    print(
        f"{'Method':<13} {'Query type':<8} {'Total time (s)':>15} "
        f"{'Avg comparisons':>16} {'Max comparisons':>17}"
    )
    print("-" * 74)

    measurements = {}
    query_groups = (("valid", valid_queries), ("invalid", invalid_queries))
    search_methods = (
        ("Sequential", sequential_find, codes),
        ("Binary", find_airport, sorted_codes),
    )

    for method_name, search_function, search_codes in search_methods:
        for query_type, queries in query_groups:
            elapsed, comparison_counts = measure_search(
                search_function, search_codes, queries
            )
            measurements[(method_name, query_type)] = (elapsed, comparison_counts)
            average = sum(comparison_counts) / len(comparison_counts)
            maximum = max(comparison_counts)
            print(
                f"{method_name:<13} {query_type:<8} {elapsed:15.6f} "
                f"{average:16.2f} {maximum:17d}"
            )

    return measurements


def report_theory(code_count):
    binary_maximum = math.ceil(math.log2(code_count + 1)) if code_count else 0
    sequential_valid_average = (code_count + 1) / 2 if code_count else 0

    print("\nTheory and measured comparisons:")
    print(f"n = {code_count}")
    print("Sequential search: O(n); binary search: O(log n).")
    print(
        "Binary-search worst case: ceil(log2(n + 1)) = "
        f"{binary_maximum} midpoint probes."
    )
    print(
        "Sequential valid-query average: (n + 1) / 2 = "
        f"{sequential_valid_average:.2f} comparisons."
    )
    print(
        f"Sequential invalid-query comparisons: n = {code_count}."
    )
    print(
        "The measured runtimes should agree with the comparison counts in trend: "
        "fewer binary-search comparisons should mean faster lookups. They will "
        "not match in exact proportion because timings also include interpreter "
        "overhead, memory/cache effects, and operating-system scheduling."
    )


def report_break_even(codes, measurements, sort_seconds):
    sequential_seconds = sum(
        measurements[("Sequential", query_type)][0]
        for query_type in ("valid", "invalid")
    )
    binary_seconds = sum(
        measurements[("Binary", query_type)][0]
        for query_type in ("valid", "invalid")
    )
    total_queries = 2 * QUERY_COUNT_PER_TYPE
    sequential_average = sequential_seconds / total_queries
    binary_average = binary_seconds / total_queries
    savings_per_lookup = sequential_average - binary_average

    print("\nSort-once break-even estimate:")
    print(f"Selection-sort time: {sort_seconds:.6f} seconds")
    print(f"Measured sequential time per lookup: {sequential_average:.9f} seconds")
    print(f"Measured binary time per lookup:     {binary_average:.9f} seconds")

    if savings_per_lookup <= 0:
        print(
            "No break-even point from this timing run: binary search did not "
            "show a per-lookup time advantage."
        )
        return

    lookups_needed = math.floor(sort_seconds / savings_per_lookup) + 1
    print(
        "Estimated lookups until sorting once and using binary search is faster: "
        f"{lookups_needed}"
    )
    print(
        "For a site with repeated lookups, paying the sort cost once at load time "
        "lets each later lookup use the faster binary search."
    )


def main():
    _, _, edges, _ = load_us_network()
    codes = build_codes(edges)

    sort_start = time.perf_counter()
    sorted_codes = selection_sort_codes(codes)
    sort_seconds = time.perf_counter() - sort_start

    print(f"Routed airport codes: {len(codes)}")
    print(f"Own selection-sort time: {sort_seconds:.6f} seconds")

    for code in TRACE_CODES:
        binary_index, binary_comparisons = trace_binary_search(sorted_codes, code)
        sequential_index, sequential_comparisons = sequential_find(codes, code)
        found_by_binary = binary_index >= 0
        found_by_sequential = sequential_index >= 0
        consistent = found_by_binary == found_by_sequential
        if found_by_binary:
            consistent = consistent and sorted_codes[binary_index] == codes[sequential_index]
        print(
            f"Final {code}: binary index={binary_index}, "
            f"comparisons={binary_comparisons}; "
            f"sequential index={sequential_index}, "
            f"comparisons={sequential_comparisons}; "
            f"results_match={consistent}"
        )
        if not consistent:
            raise AssertionError(f"Search methods disagree for {code}")

    valid_queries, invalid_queries = make_queries(codes)
    measurements = print_results_table(
        codes, sorted_codes, valid_queries, invalid_queries
    )
    report_theory(len(codes))
    report_break_even(codes, measurements, sort_seconds)


if __name__ == "__main__":
    main()
