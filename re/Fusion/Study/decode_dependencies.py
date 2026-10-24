"""Observed paired dependency tables and component-scope datum references.

Most edge flags retain their numeric values without guessed meanings. The
observed 4096 scope edge resolves through a separate typed datum to its native
component definition, independently of the feature's input geometry.
"""

from collections import Counter
import struct

from decode_sketch import reference


GRAPH_GUID = "B13113CC-031E-4F93-8240-C4C10728869F"
SCOPE_GUID = "5D15E992-1E93-4D79-A553-10D2624148AE"


def adjacency(body, cursor):
    count = struct.unpack_from("<I", body, cursor)[0]
    cursor += 4
    if count > 100000:
        raise ValueError("Dependency node count exceeds the supported limit")
    rows, seen = [], set()
    for _ in range(count):
        identity = reference(body, cursor)
        size = struct.unpack_from("<I", body, cursor+11)[0]
        cursor += 15
        if identity in seen or size > 100000 or cursor+size*15 > len(body):
            raise ValueError("Duplicate dependency node or truncated edge table")
        seen.add(identity)
        edges = []
        for _ in range(size):
            target = reference(body, cursor)
            flags = struct.unpack_from("<I", body, cursor+11)[0]
            cursor += 15
            edges.append({"object_id": target, "stored_flags": flags})
        rows.append({"object_id": identity, "edges": edges})
    return rows, cursor


def scope_datum(body, identity, components):
    if body[:3] != b"\0\0\x01" or body[14:17] != b"\x01\0\0":
        raise ValueError("Unsupported component-scope datum prefix")
    component = reference(body, 3)
    if component not in components:
        raise ValueError("Scope datum component definition is unresolved")
    anchor = reference(body, 17)
    cursor = 28
    if body[cursor] == 0:
        related, cursor = None, cursor+1
    else:
        related, cursor = reference(body, cursor), cursor+11
    if body[cursor:] != b"\0":
        raise ValueError("Unrecognized component-scope datum suffix")
    return {"object_id": identity, "component_object_id": component,
            "component_name": components[component]["name"], "anchor_object_id": anchor,
            "optional_related_object_id": related}


def decode_dependencies(data, records, features, assembly):
    components = {c["object_id"]: c for c in assembly["components"]}
    declared = {r.object_id for r in records}
    by_feature = {f["object_id"]: f for f in features}
    scopes, graphs, unresolved = {}, [], []
    for record in records:
        if record.class_guid != SCOPE_GUID:
            continue
        try:
            scopes[record.object_id] = scope_datum(data[record.body:record.end], record.object_id, components)
        except (ValueError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "reason": str(error)})
    for record in records:
        if record.class_guid != GRAPH_GUID:
            continue
        body = data[record.body:record.end]
        try:
            if body[:2] != b"\0\0" or body[2] not in (0, 1):
                raise ValueError("Unrecognized dependency table prefix")
            forward, cursor = adjacency(body, 3)
            owner = reference(body, cursor)
            reverse, cursor = adjacency(body, cursor+11)
            if body[2] == 0 and (forward or reverse):
                raise ValueError("Unsupported inactive/nonempty dependency table")
            if cursor != len(body):
                raise ValueError("Unconsumed bytes after dependency tables")
            edges = Counter((row["object_id"], edge["object_id"], edge["stored_flags"])
                            for row in forward for edge in row["edges"])
            inverse = Counter((edge["object_id"], row["object_id"], edge["stored_flags"])
                              for row in reverse for edge in row["edges"])
            if edges != inverse:
                raise ValueError("Forward/reverse dependency tables do not agree")
            if any(a not in declared or b not in declared for a, b, _ in edges):
                raise ValueError("Dependency table references an unindexed object")
            graphs.append({"object_id": record.object_id, "owner_object_id": owner,
                           "forward": forward, "reverse": reverse, "edge_count": sum(edges.values()),
                           "validation": "Forward/reverse edges and flags match as multisets"})
            for row in forward:
                feature = by_feature.get(row["object_id"])
                if feature is None:
                    continue
                feature.setdefault("native_dependency_tables", []).append({
                    "graph_object_id": record.object_id, "edges": row["edges"]})
                candidates = [scopes[e["object_id"]] for e in row["edges"]
                              if e["stored_flags"] == 4096 and e["object_id"] in scopes]
                if len(candidates) != 1:
                    continue
                scope = candidates[0]
                previous = feature.get("component_object_id")
                if previous is not None and previous != scope["component_object_id"]:
                    raise ValueError("Feature scope disagrees with independently decoded component ownership")
                evidence = feature.setdefault("component_ownership_evidence", [])
                for item in (feature.get("component_association"), "Explicit dependency scope edge and typed component datum"):
                    if item and item not in evidence:
                        evidence.append(item)
                feature.update(component_object_id=scope["component_object_id"], component_name=scope["component_name"],
                               component_scope_object_id=scope["object_id"],
                               component_association="Explicit dependency scope edge and typed component datum",
                               component_ownership_status="Observed native component-scope reference decoded")
        except (ValueError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "reason": str(error)})
    return {"graphs": graphs, "component_scope_datums": list(scopes.values()), "unresolved": unresolved,
            "features_without_component_owner": [f["object_id"] for f in features if "component_object_id" not in f],
            "scope": "Observed paired tables and component-scope edges; other edge flags remain uninterpreted"}
