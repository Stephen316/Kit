from collections import Counter
from dataclasses import replace
from itertools import product
from math import isclose, prod

from PairedCaptureIntake import require, sha256

from convert.adapters.solidworks.container.Parasolid import decode_brep_model, decode_partition_stream
from convert.adapters.solidworks.core.partition.PartMass import ReadPartMass
from convert.adapters.solidworks.core.partition.PartTopology import LinearPartBox
from interchange.geometry.models.Transform import KTransformIdentity


PARTITION = "Contents/Config-0-Partition"
RESOLVED = "Contents/Config-0-ResolvedFeatures"
TOPOLOGY = ("regions", "shell_uses", "shells", "face_uses", "faces", "loops", "coedges", "edges", "vertices")


def referenced(records, identities):
    lookup = {record.id: record for record in records}
    return tuple(lookup[key] for key in dict.fromkeys(identities) if key)


def region_model(model, region, carrier):
    shell_uses = referenced(model.shell_uses, region.shell_use_ids)
    shells = referenced(model.shells, (use.shell_id for use in shell_uses))
    face_uses = referenced(model.face_uses, (key for shell in shells for key in shell.face_use_ids))
    faces = referenced(model.faces, (use.face_id for use in face_uses))
    loops = referenced(model.loops, (key for face in faces for key in face.loop_ids))
    coedges = referenced(model.coedges, (key for loop in loops for key in loop.coedge_ids))
    edges = referenced(model.edges, (coedge.edge_id for coedge in coedges))
    vertices = referenced(model.vertices, (key for edge in edges for key in (edge.start_vertex_id, edge.end_vertex_id)))
    subset = replace(
        model, regions=(region,), shell_uses=shell_uses, shells=shells, face_uses=face_uses, faces=faces,
        loops=loops, coedges=coedges, edges=edges, vertices=vertices,
        bodies=(replace(carrier, region_ids=(region.id,)),),
        curves=referenced(model.curves, (edge.curve_id for edge in edges)),
        pcurves=referenced(model.pcurves, (coedge.pcurve_id for coedge in coedges)),
        surfaces=referenced(model.surfaces, (face.surface_id for face in faces)),
    )
    require(not subset.validate(), "automatic scope region has unresolved topology references")
    return subset


def coordinate(point):
    return (point.x, point.y, point.z)


def match_vector(observed, expected, tolerance):
    return all(isclose(v, target, rel_tol=0, abs_tol=tolerance) for v, target in zip(observed, expected, strict=True))


def read_scope_support_sheet(blob, prefix, spec):
    span = prefix["cut_sketch"]["kernel_packet"]
    raw = blob[span["start"]:span["end"]]
    parts = decode_partition_stream(raw, RESOLVED)
    require(len(parts) == 1, "expected one wrapped Cut support payload")
    (packet,) = parts
    require(
        packet.wrapper_offset == 1 and raw[0] == 0 and packet.stored_size == len(raw) - 1,
        "wrapped Cut support does not consume its bounded payload",
    )
    model = decode_brep_model(packet.data)
    require(
        model is not None and not model.validate() and len(model.regions) == len(model.shells) == len(model.bodies)
        == len(model.faces) == len(model.surfaces) == len(model.loops) == 1
        and not model.regions[0].solid and not model.shells[0].closed
        and len(model.edges) == len(model.vertices) == 4 and not model.wires,
        "bounded Cut support is not a single four-edge sheet",
    )
    require(LinearPartBox(model) is not None, "scope support sheet is not planar and straight-edged")
    face, surface = model.faces[0], model.surfaces[0]
    require(face.surface_id == surface.id, "scope support face does not resolve its plane")
    reference = prefix["cut_support"]["plane"]
    normal = tuple(value if face.same_sense else -value for value in coordinate(surface.normal))
    origin_mm = coordinate(surface.origin)
    lower, upper = spec["bodies"][spec["cut"]["support_body"]]["bounds_mm"]
    z = spec["cut"]["profile_bounds_mm"][0][2]
    expected = sorted(product((lower[0], upper[0]), (lower[1], upper[1]), (z,)))
    points = sorted(coordinate(row.point) for row in model.vertices)
    tolerance = spec["tolerances"]["length_mm_absolute"]
    require(
        normal == reference["normal_world"]
        and match_vector(origin_mm, (value * 1000 for value in reference["root_metres"]), tolerance)
        and all(match_vector(p, q, tolerance) for p, q in zip(points, expected, strict=True)),
        "bounded Cut sheet does not match the resolved support plane and its recipe cap",
    )
    return {
        **span, "stored_sha256": sha256(raw), "decoded_sha256": packet.sha256,
        "wrapper_offset": span["start"] + packet.wrapper_offset, "schema": packet.schema,
        "compressed_size": packet.compressed_size, "decoded_size": packet.uncompressed_size,
        "support_face_id": face.id, "origin_mm": origin_mm, "effective_normal_world": normal,
        "points_mm": points,
    }


def cap_openings(model, body_bounds, cut_bounds, tolerance):
    vertices = {row.id: coordinate(row.point) for row in model.vertices}
    edges = {row.id: row for row in model.edges}
    coedges = {row.id: row.edge_id for row in model.coedges}
    loops = {row.id: row for row in model.loops}
    caps = [face for face in model.faces if len(face.loop_ids) > 1]
    require(len(caps) == 2, "automatic scope region does not have two cap faces with openings")
    openings = {}
    for face in caps:
        require(len(face.loop_ids) == 2, "automatic scope cap does not have two boundary rings")
        rings = []
        for loop in (loops[key] for key in face.loop_ids):
            boundary = [edges[coedges[key]] for key in loop.coedge_ids]
            points = {vertices[key] for edge in boundary for key in (edge.start_vertex_id, edge.end_vertex_id)}
            require(len(boundary) == len(points) == 4, "automatic scope cap is not bounded by four-edge rings")
            rings.append({"loop_id": loop.id, "decoded_outer": loop.outer, "points_mm": sorted(points)})
        cap_z = rings[0]["points_mm"][0][2]
        elevations = [target for target in (corner[2] for corner in body_bounds)
                      if isclose(cap_z, target, rel_tol=0, abs_tol=tolerance)]
        require(len(elevations) == 1 and elevations[0] not in openings, "automatic scope cap does not match a distinct box end")
        z = elevations[0]
        profile = []
        for bounds in (body_bounds, cut_bounds):
            low, high = bounds
            expected = sorted(product((low[0], high[0]), (low[1], high[1]), (z,)))
            matched = [
                ring for ring in rings
                if all(match_vector(point, target, tolerance)
                       for point, target in zip(ring["points_mm"], expected, strict=True))
            ]
            require(len(matched) == 1, "automatic scope cap ring differs from the box perimeter or cut rectangle")
            profile.append(matched[0])
        openings[z] = {"face_id": face.id, "perimeter": profile[0], "opening": profile[1]}
    return [openings[z] for z in sorted(openings)]


def describe_region(model, expected, cut_bounds, tolerance):
    bounds = LinearPartBox(model)
    require(bounds is not None, "automatic scope region has a non-planar or non-linear boundary")
    mass = ReadPartMass(model, bounds)
    require(mass is not None, "automatic scope region has no positive closed-shell measure")
    lower, upper = (coordinate(bounds.minimum), coordinate(bounds.maximum))
    corners = (lower, upper)
    length = tolerance["length_mm_absolute"]
    candidates = [
        body for body, settings in expected.items()
        if all(match_vector(left, right, length) for left, right in zip(corners, settings["bounds_mm"], strict=True))
    ]
    require(len(candidates) == 1, "automatic scope region does not uniquely match the authored box")
    label = candidates[0]
    outer_min, outer_max = expected[label]["bounds_mm"]
    cut_min, cut_max = cut_bounds
    require(
        all(a < c < d < b for a, b, c, d in zip(outer_min[:2], outer_max[:2], cut_min[:2], cut_max[:2], strict=True))
        and outer_max[2] <= cut_min[2] == cut_max[2],
        "automatic scope recipe does not cut the entire box thickness with one inner rectangle",
    )
    holes = cap_openings(model, (outer_min, outer_max), cut_bounds, length)
    outer = prod(b - a for a, b in zip(outer_min, outer_max, strict=True))
    hole_min, hole_max = (*cut_min[:2], outer_min[2]), (*cut_max[:2], outer_max[2])
    removed = prod(b - a for a, b in zip(hole_min, hole_max, strict=True))
    expected_volume = outer - removed
    expected_centre = tuple(
        (outer * (a + b) - removed * (c + d)) / (2 * expected_volume)
        for a, b, c, d in zip(outer_min, outer_max, hole_min, hole_max, strict=True)
    )
    require(
        isclose(mass.Volume, expected_volume, rel_tol=tolerance["volume_relative"],
                abs_tol=tolerance["volume_mm3_absolute"])
        and match_vector(mass.Centroid, expected_centre, length),
        "automatic scope region measure disagrees with the independently calculated box minus hole",
    )
    return label, {
        "region_id": model.regions[0].id, "bounds_mm": corners, "volume_mm3": mass.Volume,
        "centroid_mm": mass.Centroid, "expected_volume_mm3": expected_volume, "expected_centroid_mm": expected_centre,
        "face_count": len(model.faces), "edge_count": len(model.edges), "vertex_count": len(model.vertices),
        "cap_openings": holes,
    }


def read_scope_partition(archive, spec, scope_bodies):
    raw = archive.require(PARTITION)
    partitions = [payload.data for payload in decode_partition_stream(raw, PARTITION) if payload.kind == "partition"]
    require(len(partitions) == 1, "expected one saved active scope partition")
    (payload,) = partitions
    model = decode_brep_model(payload)
    require(
        model is not None and not model.validate() and len(model.bodies) == 1
        and len(model.regions) == len(spec["bodies"]) == 2 and not model.wires,
        "expected one decoded topology carrier holding the two scoped regions",
    )
    (carrier,) = model.bodies
    require(
        carrier.transform == KTransformIdentity and not carrier.wire_ids and not carrier.vertex_ids
        and set(carrier.region_ids) == {region.id for region in model.regions},
        "unexpected carrier around the saved scoped regions",
    )
    subsets = [region_model(model, region, carrier) for region in model.regions]
    require(
        all(Counter(node.id for sub in subsets for node in getattr(sub, name))
            == Counter(node.id for node in getattr(model, name)) for name in TOPOLOGY),
        "some saved scoped topology is shared across regions or unaccounted for",
    )
    regions = dict(
        describe_region(sub, spec["bodies"], spec["cut"]["profile_bounds_mm"], spec["tolerances"])
        for sub in subsets
    )
    require(set(regions) == spec["bodies"].keys(), "active partition did not match both scoped recipe bodies")
    for scope in scope_bodies:
        regions[scope["producer_candidate"]]["resolved_scope"] = {
            key: scope[key] for key in ("body_id", "feature_id", "recent_atom_id")
        }
    return {
        "stream": PARTITION, "stream_sha256": sha256(raw), "partition_sha256": sha256(payload),
        "decoded_carrier_id": carrier.id, "region_binding": "matching_distinct_recipe_bounds", "regions": regions,
    }
