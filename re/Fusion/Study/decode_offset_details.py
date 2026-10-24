"""Observed offset Line endpoint incidence and Circle center correspondence.

Run after decode_sketches. This reads native references, not a sketch solver or
the general API isTopologyMatched flag. Offset curve style and secondary-tag
semantics remain unresolved.
"""

from collections import Counter, defaultdict
import struct

from decode_sketch import attributes, constraint_prefix, reference, same


OFFSET = "afc07c10-99ac-5304-ae1b-dbee335b0e43"
SIDE = "04e598ff-2979-5e41-8bc0-5c435c810909"
ASSOCIATION = "D3BD153B-EB8A-405E-9D29-69EE0C3D227C"
LINE = "DCA267ED-D615-4934-B64F-AD805E8003E2"
CIRCLE = "F0130424-8B7E-4092-93C9-1CA807482534"


def _line_graph(curves):
    incidence, neighbors = defaultdict(list), defaultdict(set)
    for curve in curves:
        start, end = curve["start_point_id"], curve["end_point_id"]
        if start == end:
            raise ValueError("Unobserved self-loop offset Line")
        for point, other in ((start, end), (end, start)):
            incidence[point].append(curve["object_id"])
            neighbors[point].add(other)
    if any(len(edges) > 2 for edges in incidence.values()):
        raise ValueError("Unobserved branched offset Line graph")
    remaining, components = set(incidence), []
    while remaining:
        pending, visited = [min(remaining)], set()
        while pending:
            point = pending.pop()
            if point not in visited:
                visited.add(point)
                pending.extend(neighbors[point]-visited)
        remaining -= visited
        endpoints = sorted(p for p in visited if len(incidence[p]) == 1)
        if len(endpoints) not in (0, 2):
            raise ValueError("Unobserved offset Line component incidence")
        components.append({"point_object_ids": sorted(visited),
                           "curve_object_ids": sorted({e for p in visited for e in incidence[p]}),
                           "open_endpoint_ids": endpoints,
                           "is_closed_by_shared_endpoint_references": not endpoints})
    return {"vertex_count": len(incidence), "edge_count": len(curves),
            "components": components,
            "incidence": [{"point_object_id": p, "curve_object_ids": sorted(edges)}
                          for p, edges in sorted(incidence.items())]}


def decode_offset_details(data, records, features):
    """Attach offset_details to observed OffsetCurves constraints atomically."""
    grouped = defaultdict(list)
    for record in records:
        if record.is_primary:
            grouped[record.object_id].append(record)

    def typed(identity, guid):
        matches = grouped.get(identity, [])
        if len(matches) != 1 or matches[0].class_guid != guid:
            raise ValueError("Offset detail typed reference unresolved or ambiguous")
        record = matches[0]
        return data[record.body:record.end]

    def side(identity, role, opposite):
        body = typed(identity, SIDE)
        count = struct.unpack_from("<I", body, 1)[0]
        cursor = 5+15*count
        if (body[0] != 1 or not 1 <= count <= 1024 or len(body) != cursor+16
                or body[cursor] != 0 or reference(body, cursor+1) != opposite
                or struct.unpack_from("<I", body, cursor+12)[0] != role):
            raise ValueError("Unsupported offset detail side layout/reciprocity")
        identities = [reference(body, 5+15*i) for i in range(count)]
        if len(set(identities)) != len(identities):
            raise ValueError("Duplicate offset detail side entity")
        return identities

    decoded, unresolved = [], []
    for sketch in features:
        if sketch["kind"] != "Sketch":
            continue
        owner = sketch["sketch_object_id"]
        entities = {g["object_id"]: g for g in sketch["geometry"]}
        for constraint in sketch["constraints"]:
            if constraint["kind"] != "OffsetCurves":
                continue
            identity = constraint["object_id"]
            try:
                body = typed(identity, OFFSET)
                if (len(body) != 176 or body[:5] != bytes.fromhex("0105000000")
                        or reference(body, 135) != owner):
                    raise ValueError("Unsupported offset detail controller/owner")
                parent_side, child_side = reference(body, 146), reference(body, 102)
                parents = side(parent_side, 1, child_side)
                children = side(child_side, 2, parent_side)
                if parents != constraint["parent_entity_ids"] or children != constraint["child_entity_ids"]:
                    raise ValueError("Offset detail source side lists disagree")
                assoc = typed(reference(body, 113), ASSOCIATION)
                deps, props, cursor = constraint_prefix(assoc)
                count = struct.unpack_from("<I", assoc, cursor+19)[0]
                if (props != {"EntityGenesis": 32} or reference(assoc, cursor) != owner
                        or struct.unpack_from("<Q", assoc, cursor+11)[0] != 0x2000000000
                        or count != 2*len(parents) or len(children) != len(parents)
                        or len(assoc) != cursor+24+11*count or assoc[-1] != 0):
                    raise ValueError("Unsupported offset detail association")
                copied = [reference(assoc, cursor+23+11*i) for i in range(count)]
                pairs = list(zip(copied[::2], copied[1::2]))
                if (Counter(copied) != Counter(deps) or Counter(copied[::2]) != Counter(parents)
                        or Counter(copied[1::2]) != Counter(children)
                        or pairs != [tuple(p) for p in constraint["stored_pairs"]]):
                    raise ValueError("Offset detail native pair copies disagree")
                curve_details = []
                for curve_id in parents+children:
                    curve = entities[curve_id]
                    kind = curve["kind"]
                    if kind not in ("Line", "Circle"):
                        raise ValueError("Unobserved offset detail curve kind")
                    raw = typed(curve_id, LINE if kind == "Line" else CIRCLE)
                    props, start = attributes(raw, 2)
                    expected_side = parent_side if curve_id in parents else child_side
                    if (raw[:2] != b"\0\1" or len(raw)-start != (182 if kind == "Line" else 173)
                            or reference(raw, len(raw)-11) != owner
                            or reference(raw, len(raw)-48) != expected_side
                            or curve.get("offset_side_record_object_id") != expected_side
                            or props["crv_primary_id"] != curve["entity_tag"]
                            or props["crv_secondary_id"] != curve["secondary_entity_tag"]):
                        raise ValueError("Offset detail curve owner/side/tag disagrees")
                    roles = (("end_point_id", 96), ("start_point_id", 107)) if kind == "Line" else (("center_point_id", 96),)
                    for field, offset in roles:
                        point_id = reference(raw, start+offset)
                        point = entities[point_id]
                        if point_id != curve[field] or point["kind"] != "Point" or point["sketch_object_id"] != owner:
                            raise ValueError("Offset detail point reference disagrees")
                        position_field = {"start_point_id": "start_cm", "end_point_id": "end_cm", "center_point_id": "center_cm"}[field]
                        if not same(point["position_cm"], curve[position_field]):
                            raise ValueError("Offset detail point coordinate copy disagrees")
                    curve_details.append({"object_id": curve_id, "side_record_object_id": expected_side,
                                          "primary_entity_tag": props["crv_primary_id"],
                                          "secondary_entity_tag": props["crv_secondary_id"],
                                          "uninterpreted_u32_fields": [
                                              {"offset_from_body_end": offset, "value": struct.unpack_from("<I", raw, len(raw)+offset)[0]}
                                              for offset in (-62, -57)],
                                          "style_and_secondary_tag_status": "Unknown semantics; no API state contrasts captured"})
                kinds = {entities[p]["kind"] for pair in pairs for p in pair}
                result = {"object_id": identity, "sketch_object_id": owner, "curve_records": curve_details,
                          "endpoint_correspondence": [], "center_correspondence": [],
                          "topology_flag_status": "API isTopologyMatched native flag unresolved; incidence is computed from explicit references"}
                if kinds == {"Line"}:
                    mapping = {}
                    for parent_id, child_id in pairs:
                        parent, child = entities[parent_id], entities[child_id]
                        for field in ("start_point_id", "end_point_id"):
                            p, c = parent[field], child[field]
                            if p in mapping and mapping[p] != c:
                                raise ValueError("Offset paired endpoint orientation is inconsistent")
                            mapping[p] = c
                    if len(set(mapping.values())) != len(mapping):
                        raise ValueError("Offset endpoint correspondence is not injective")
                    parent_graph = _line_graph([entities[p] for p in parents])
                    child_graph = _line_graph([entities[c] for c in children])
                    child_incidence = {i["point_object_id"]: set(i["curve_object_ids"]) for i in child_graph["incidence"]}
                    edge_map = dict(pairs)
                    for incident in parent_graph["incidence"]:
                        if {edge_map[e] for e in incident["curve_object_ids"]} != child_incidence[mapping[incident["point_object_id"]]]:
                            raise ValueError("Offset endpoint map does not preserve curve incidence")
                    if len(mapping) != parent_graph["vertex_count"] or len(mapping) != child_graph["vertex_count"]:
                        raise ValueError("Offset endpoint map is not onto both graphs")
                    result.update(parent_line_graph=parent_graph, child_line_graph=child_graph,
                                  endpoint_correspondence=[{"parent_point_object_id": p, "child_point_object_id": c} for p, c in sorted(mapping.items())],
                                  correspondence_scope="Stored start-to-start/end-to-end orientation on paired Lines; shared endpoint incidence verified")
                elif kinds == {"Circle"}:
                    if len(pairs) != 1:
                        raise ValueError("Unobserved multiple-circle offset detail graph")
                    parent, child = (entities[p] for p in pairs[0])
                    result["center_correspondence"] = [{"parent_point_object_id": parent["center_point_id"],
                                                        "child_point_object_id": child["center_point_id"],
                                                        "same_cached_position": same(parent["center_cm"], child["center_cm"])}]
                    result["correspondence_scope"] = "Stored Circle center references; closed primitives have no endpoint graph"
                else:
                    raise ValueError("Unobserved mixed offset detail graph")
                constraint["offset_details"] = result
                decoded.append(result)
            except (ValueError, KeyError, IndexError, struct.error) as error:
                unresolved.append({"object_id": identity, "sketch_object_id": owner, "reason": str(error)})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Observed Line endpoint incidence and Circle centers; no solver, style flag or general topology flag decoding"}
