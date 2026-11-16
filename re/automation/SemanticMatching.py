import json
import math
from collections import Counter, defaultdict

QUANTITIES = frozenset(
    {"length_mm", "angle_rad", "dimensionless", "area_mm2", "volume_mm3", "exact"}
)
DIMENSIONAL = QUANTITIES - {"dimensionless", "exact"}
MAX_NODES = 100000
MAX_RECORDS = 1000000


def _text(value, limit, description):
    if not isinstance(value, str) or not value or len(value) > limit:
        raise ValueError(f"{description} must be a nonempty bounded string")
    return value


def _profile(tolerances):
    if not isinstance(tolerances, dict) or set(tolerances) - QUANTITIES:
        raise ValueError("tolerances must name supported quantities")
    values = {}
    for quantity, value in tolerances.items():
        if type(value) not in (int, float):
            raise ValueError("tolerances must be finite nonnegative numbers")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite or value < 0 or (quantity == "exact" and value != 0):
            raise ValueError(
                "tolerances must be finite nonnegative and exact stays zero"
            )
        values[quantity] = value
    return values


def _graph(graph, side):
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), dict):
        raise ValueError(f"{side} graph must have an identity keyed node mapping")
    nodes = graph["nodes"]
    if len(nodes) > MAX_NODES:
        raise ValueError("semantic graph exceeds its node limit")
    records = 0
    for identity, node in nodes.items():
        _text(identity, 4096, "node identity")
        if not isinstance(node, dict):
            raise ValueError("semantic nodes must be objects")
        _text(node.get("kind"), 512, "node kind")
        fields, links = node.get("fields"), node.get("links")
        if not isinstance(fields, dict) or not isinstance(links, list):
            raise ValueError("semantic nodes require fields and links")
        records += len(fields) + len(links)
        if records > MAX_RECORDS:
            raise ValueError("semantic graph exceeds its field and reference limit")
        for pointer, atom in fields.items():
            if (
                not isinstance(pointer, str)
                or len(pointer) > 4096
                or (pointer and not pointer.startswith("/"))
                or "~" in pointer.replace("~0", "").replace("~1", "")
            ):
                raise ValueError("semantic field paths must be JSON pointers")
            if not isinstance(atom, dict) or set(atom) != {"quantity", "value"}:
                raise ValueError("semantic fields require a value and quantity")
            if (
                not isinstance(atom["quantity"], str)
                or atom["quantity"] not in QUANTITIES
            ):
                raise ValueError("semantic field has an unsupported quantity")
            value = atom["value"]
            if value is not None and type(value) not in (bool, int, float, str):
                raise ValueError("semantic field values must be JSON primitives")
            if isinstance(value, str) and len(value) > 1024 * 1024:
                raise ValueError("semantic field string exceeds its character limit")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError("semantic field numbers must be finite")
            if atom["quantity"] != "exact" and type(value) is int:
                try:
                    finite = math.isfinite(value)
                except OverflowError:
                    finite = False
                if not finite:
                    raise ValueError("numeric semantic quantities must be finite")
        for link in links:
            if not isinstance(link, dict) or set(link) != {"role", "target"}:
                raise ValueError("semantic references require role and target")
            _text(link["role"], 4096, "reference role")
            _text(link["target"], 4096, "reference target")
    issues = graph.get("issues", [])
    if not isinstance(issues, list) or len(issues) > MAX_RECORDS:
        raise ValueError("semantic graph issues must be a bounded list")
    try:
        encoded = json.dumps(issues, allow_nan=False, ensure_ascii=False)
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError(
            "semantic graph issues must contain finite JSON data"
        ) from error
    if len(encoded) > 32 * 1024 * 1024:
        raise ValueError("semantic graph issues exceed their output budget")
    return nodes, [{"side": side, "issue": item} for item in issues]


def _equal(left, right, tolerances):
    if left["quantity"] != right["quantity"]:
        return False
    first, second = left["value"], right["value"]
    quantity = left["quantity"]
    numeric = type(first) in (int, float) and type(second) in (int, float)
    tolerant = quantity in DIMENSIONAL or (
        quantity == "dimensionless" and type(first) is type(second) is float
    )
    if numeric and tolerant:
        return abs(first - second) <= tolerances.get(quantity, 0)
    return type(first) is type(second) and first == second


def _fields(left, right, tolerances):
    differences = []
    for pointer in sorted(left.keys() | right.keys()):
        first, second = left.get(pointer), right.get(pointer)
        if first is None:
            reason = "missing_left"
        elif second is None:
            reason = "missing_right"
        elif first["quantity"] != second["quantity"]:
            reason = "quantity"
        elif not _equal(first, second, tolerances):
            reason = "value"
        else:
            continue
        differences.append(
            {
                "pointer": pointer,
                "left": None if first is None else dict(first),
                "right": None if second is None else dict(second),
                "reason": reason,
            }
        )
    return differences


def _neighbors(nodes):
    neighbors = {identity: Counter() for identity in nodes}
    for identity, node in nodes.items():
        for link in node["links"]:
            target, role = link["target"], link["role"]
            neighbors[identity][("out", role, target)] += 1
            if target in nodes:
                neighbors[target][("in", role, identity)] += 1
    signatures = {}
    for identity, links in neighbors.items():
        signatures[identity] = Counter()
        for (direction, role, target), count in links.items():
            kind = (
                "self"
                if target == identity
                else (
                    ("node", nodes[target]["kind"]) if target in nodes else "unresolved"
                )
            )
            signatures[identity][(direction, role, kind)] += count
    return neighbors, signatures


def _distance(left, right):
    return sum((left - right).values()) + sum((right - left).values())


def _mapped_neighbors(links, correspondence, right_side=False):
    result = Counter()
    for (direction, role, target), count in links.items():
        if target in correspondence:
            mapped = target if right_side else correspondence[target]
            result[(direction, role, mapped)] += count
    return result


def _preferences(scores):
    left, right = defaultdict(list), defaultdict(list)
    for (first, second), score in scores.items():
        left[first].append((score, second))
        right[second].append((score, first))
    preferred = []
    alternatives = {}
    for first, options in left.items():
        best = min(score for score, _ in options)
        targets = [second for score, second in options if score == best]
        alternatives[first] = sorted(targets)
        if len(targets) != 1:
            continue
        second = targets[0]
        best_reverse = min(score for score, _ in right[second])
        sources = [source for score, source in right[second] if score == best_reverse]
        if sources == [first]:
            preferred.append((first, second))
    return preferred, alternatives


def _reference_differences(left, right, matches):
    differences = []
    inverse = {target: source for source, target in matches.items()}
    for first, second in sorted(matches.items()):
        expected, observed = Counter(), Counter()
        for link in left[first]["links"]:
            target = link["target"]
            token = (
                ("matched", matches[target]) if target in matches else ("left", target)
            )
            expected[(link["role"], *token)] += 1
        for link in right[second]["links"]:
            target = link["target"]
            token = ("matched", target) if target in inverse else ("right", target)
            observed[(link["role"], *token)] += 1
        for key in sorted(expected.keys() | observed.keys()):
            if expected[key] == observed[key]:
                continue
            role, origin, target = key
            differences.append(
                {
                    "left": first,
                    "right": second,
                    "role": role,
                    "left_target": (
                        inverse[target]
                        if origin == "matched"
                        else target if origin == "left" else None
                    ),
                    "right_target": target if origin in {"matched", "right"} else None,
                    "left_count": expected[key],
                    "right_count": observed[key],
                    "reason": (
                        "target_multiplicity"
                        if origin == "matched"
                        else "unmatched_target"
                    ),
                }
            )
    for side, nodes, aligned in (("left", left, matches), ("right", right, inverse)):
        for identity, node in sorted(nodes.items()):
            counts = Counter((link["role"], link["target"]) for link in node["links"])
            for (role, target), count in sorted(counts.items()):
                if target not in nodes or identity not in aligned:
                    differences.append(
                        {
                            "side": side,
                            "node": identity,
                            "role": role,
                            "target": target,
                            "count": count,
                            "reason": (
                                "unresolved_target"
                                if target not in nodes
                                else "unmatched_node"
                            ),
                        }
                    )
    return differences


def match_graphs(left, right, tolerances, max_candidates=100000):
    if type(max_candidates) is not int or not 1 <= max_candidates <= 1000000:
        raise ValueError("max_candidates must be an integer from 1 through 1000000")
    tolerances = _profile(tolerances)
    left_nodes, left_issues = _graph(left, "left")
    right_nodes, right_issues = _graph(right, "right")
    left_links, left_shapes = _neighbors(left_nodes)
    right_links, right_shapes = _neighbors(right_nodes)
    left_kinds, right_kinds = defaultdict(list), defaultdict(list)
    for identity, node in left_nodes.items():
        left_kinds[node["kind"]].append(identity)
    for identity, node in right_nodes.items():
        right_kinds[node["kind"]].append(identity)
    candidates, differences, limited = {}, {}, []
    evaluations = 0
    work_remaining = max_candidates * 64
    for kind in sorted(left_kinds.keys() & right_kinds.keys()):
        sources, targets = sorted(left_kinds[kind]), sorted(right_kinds[kind])
        count = len(sources) * len(targets)
        work = len(targets) * sum(
            len(left_nodes[first]["fields"]) + len(left_shapes[first]) + 1
            for first in sources
        ) + len(sources) * sum(
            len(right_nodes[second]["fields"]) + len(right_shapes[second]) + 1
            for second in targets
        )
        if count > max_candidates - evaluations or work > work_remaining:
            limited.append(
                {
                    "kind": kind,
                    "left": sources,
                    "right": targets,
                    "candidate_pairs": count,
                    "reason": (
                        "candidate_budget"
                        if count > max_candidates - evaluations
                        else "field_budget"
                    ),
                }
            )
            continue
        for first in sources:
            for second in targets:
                fields = _fields(
                    left_nodes[first]["fields"],
                    right_nodes[second]["fields"],
                    tolerances,
                )
                pair = first, second
                differences[pair] = fields
                candidates[pair] = (
                    0,
                    _distance(left_shapes[first], right_shapes[second]),
                    len(fields),
                )
        evaluations += count
        work_remaining -= work
    matches = {}
    search_limited = bool(limited)
    anchors = [
        (sources[0], right_kinds[kind][0])
        for kind, sources in left_kinds.items()
        if len(sources) == len(right_kinds.get(kind, [])) == 1
        and (sources[0], right_kinds[kind][0]) in candidates
    ]
    alternatives = {}
    while candidates:
        preferred, alternatives = _preferences(candidates)
        selected = anchors if anchors else preferred
        anchors = []
        if not selected:
            break
        matches.update(selected)
        inverse = {target: source for source, target in matches.items()}
        candidates = {
            pair: score
            for pair, score in candidates.items()
            if pair[0] not in matches and pair[1] not in inverse
        }
        if not candidates:
            alternatives = {}
            break
        work = sum(
            len(left_links[first]) + len(right_links[second]) + 1
            for first, second in candidates
        )
        if len(candidates) > max_candidates - evaluations or work > work_remaining:
            search_limited = True
            alternatives = {}
            break
        mapped_left = {
            first: _mapped_neighbors(left_links[first], matches)
            for first in {pair[0] for pair in candidates}
        }
        mapped_right = {
            second: _mapped_neighbors(right_links[second], inverse, True)
            for second in {pair[1] for pair in candidates}
        }
        candidates = {
            (first, second): (
                _distance(mapped_left[first], mapped_right[second]),
                score[1],
                score[2],
            )
            for (first, second), score in candidates.items()
        }
        evaluations += len(candidates)
        work_remaining -= work
    unresolved = defaultdict(list)
    for first, second in candidates:
        unresolved[first].append(second)
    return {
        "matches": [
            {
                "left": first,
                "right": second,
                "differences": differences[(first, second)],
            }
            for first, second in sorted(matches.items())
        ],
        "ambiguous": [
            {
                "left": first,
                "right": sorted(targets),
                "preferred_right": alternatives.get(first, []),
                "reason": (
                    "non_unique_correspondence"
                    if first in alternatives
                    else "search_limit"
                ),
                "candidates": [
                    {
                        "right": second,
                        "differences": differences[(first, second)],
                        "score": {
                            "known_reference_mismatches": candidates[(first, second)][
                                0
                            ],
                            "neighborhood_mismatches": candidates[(first, second)][1],
                            "field_mismatches": candidates[(first, second)][2],
                        },
                    }
                    for second in sorted(targets)
                ],
            }
            for first, targets in sorted(unresolved.items())
        ],
        "unmatched_left": sorted(left_nodes.keys() - matches.keys()),
        "unmatched_right": sorted(right_nodes.keys() - set(matches.values())),
        "reference_differences": _reference_differences(
            left_nodes, right_nodes, matches
        ),
        "search_limited": search_limited,
        "limited_candidates": limited,
        "candidate_evaluations": evaluations,
        "issues": left_issues + right_issues,
    }
