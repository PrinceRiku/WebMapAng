def _build_adjacency(edges):
    adjacency = {}
    for source, destination in edges:
        adjacency.setdefault(source, set())
        adjacency.setdefault(destination, set())
        adjacency[source].add(destination)
        adjacency[destination].add(source)
    return adjacency


def path_exists(edges, origin, destination, verbose=False):
    """Search outward from origin by connection layers.

    Return whether destination is reachable and the number of iterations used.
    """
    adjacency = _build_adjacency(edges)
    vertices = set(adjacency)
    if origin not in vertices or destination not in vertices:
        return False, 0
    if origin == destination:
        return True, 0

    used = set()
    new = {origin}
    untouched = vertices - new
    n_iterations = 0

    while new:
        next_new = set()
        for airport in sorted(new):
            used.add(airport)
            for neighbor in adjacency[airport]:
                if neighbor in untouched:
                    untouched.remove(neighbor)
                    next_new.add(neighbor)

        new = next_new
        n_iterations += 1

        if verbose:
            print(
                f"Iteration {n_iterations}: used={sorted(used)}, "
                f"new={sorted(new)}, untouched={len(untouched)}"
            )

        if destination in new:
            return True, n_iterations

    return False, n_iterations


def connected_components(edges):
    """Return routed-airport components from largest to smallest."""
    adjacency = _build_adjacency(edges)
    untouched = set(adjacency)
    components = []

    while untouched:
        origin = min(untouched)
        component = {origin}
        new = {origin}

        while new:
            next_new = set()
            for airport in new:
                for neighbor in adjacency[airport]:
                    if neighbor in untouched and neighbor not in component:
                        component.add(neighbor)
                        next_new.add(neighbor)
            new = next_new

        untouched.difference_update(component)
        components.append(sorted(component))

    components.sort(key=lambda component: (-len(component), component[0]))
    return components


def discovery_layers(edges, origin):
    """Return airport codes mapped to their first-discovery iteration."""
    adjacency = _build_adjacency(edges)
    if origin not in adjacency:
        return {}

    layers = {origin: 0}
    used = set()
    new = {origin}
    untouched = set(adjacency) - new
    iteration = 0

    while new:
        next_new = set()
        for airport in new:
            used.add(airport)
            for neighbor in adjacency[airport]:
                if neighbor in untouched:
                    untouched.remove(neighbor)
                    next_new.add(neighbor)
                    layers[neighbor] = iteration + 1
        new = next_new
        iteration += 1

    return layers
