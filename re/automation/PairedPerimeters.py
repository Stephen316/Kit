"""Match complete undirected world-space edge perimeters without identity masking."""

import math


def edge_gap(first, second):
    forwards = max(math.dist(first[0], second[0]), math.dist(first[1], second[1]))
    backwards = max(math.dist(first[0], second[1]), math.dist(first[1], second[0]))
    return min(forwards, backwards)


def match_perimeters(first, second, tolerance):
    if not first or not second:
        return {"status": "unclassified", "reason": "missing perimeter geometry"}
    if len(first) != len(second):
        return {"status": "different", "reason": "perimeter cardinality differs"}
    if any(
        len({key for key, _ in perimeter}) != len(perimeter)
        for perimeter in (first, second)
    ):
        return {
            "status": "ambiguous",
            "reason": "perimeter repeats a local boundary identity",
        }
    candidates = [
        [(index, edge_gap(edge, peer)) for index, (_, peer) in enumerate(second)]
        for _, edge in first
    ]
    matched = [[item for item in row if item[1] <= tolerance] for row in candidates]
    if any(len(row) > 1 for row in matched):
        return {
            "status": "ambiguous",
            "reason": "multiple geometric counterparts for a boundary edge",
        }
    if any(not row for row in matched):
        return {"status": "different", "reason": "unmatched world boundary edge"}
    edges = [row[0] for row in matched]
    if len({index for index, _ in edges}) != len(second):
        return {
            "status": "ambiguous",
            "reason": "boundary correspondence is not one to one",
        }
    return {
        "status": "equal",
        "maximum_endpoint_delta_mm": max(delta for _, delta in edges),
        "matched_links": [
            [identity, second[index][0]]
            for (identity, _), (index, _) in zip(first, edges, strict=True)
        ],
    }
