"""Author and observe the independently created Fusion scope controls."""

import math


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def xyz(value):
    return tuple(value.asArray())


def volume_limit(first, second, tolerances):
    return max(
        tolerances["volume_mm3_absolute"],
        tolerances["volume_relative"] * max(abs(first), abs(second)),
    )


def near(first, second, tolerance):
    return math.dist(first, second) <= tolerance


def bounds_pair(values):
    require(
        isinstance(values, list)
        and len(values) == 2
        and all(isinstance(row, list) and len(row) == 3 for row in values)
        and all(
            type(v) in (float, int) and math.isfinite(v) for row in values for v in row
        ),
        "Expected finite XYZ bounds",
    )
    return values


def validate_spec(spec):
    require(
        set(spec)
        == {"schema", "scope", "units", "bodies", "cut", "cases", "tolerances"}
        and spec["schema"] == 1
        and spec["scope"] == "two-body-through-all-discovery"
        and spec["units"] == "mm",
        "Unsupported scope-control specification",
    )
    bodies, cut = spec["bodies"], spec["cut"]
    require(set(bodies) == {"A", "B"}, "Expected exactly two specified bodies")
    for role, name in (("A", "ScopeBossA"), ("B", "ScopeBossB")):
        body = bodies[role]
        require(
            set(body) == {"producer", "bounds_mm"} and body["producer"] == name,
            "Unexpected boss producer",
        )
        low, high = bounds_pair(body["bounds_mm"])
        require(all(left < right for left, right in zip(low, high)), "Degenerate boss")
    keys = {
        "sketch",
        "feature",
        "support_body",
        "profile_bounds_mm",
        "direction_world",
        "end_condition",
        "depth_mm",
    }
    require(
        set(cut) == keys
        and cut["sketch"] == "ScopeCutSketch"
        and cut["feature"] == "ScopeThroughAll"
        and cut["support_body"] == "A"
        and cut["direction_world"] == [0, 0, -1]
        and cut["end_condition"] == "through_all"
        and cut["depth_mm"] is None,
        "Unexpected through-all control",
    )
    low, high = bounds_pair(cut["profile_bounds_mm"])
    require(
        low[2] == high[2] == bodies["A"]["bounds_mm"][1][2]
        and bodies["B"]["bounds_mm"][1][2] < bodies["A"]["bounds_mm"][0][2]
        and all(
            body["bounds_mm"][0][axis]
            < low[axis]
            < high[axis]
            < body["bounds_mm"][1][axis]
            for body in bodies.values()
            for axis in (0, 1)
        ),
        "Scope control requires a separated stack with the full cutter inside both footprints",
    )
    require(
        spec["cases"]
        == [
            {
                "mode": "automatic",
                "input_body_ids": None,
                "expected_affected_body_ids": ["A", "B"],
            },
            {
                "mode": "explicit_a",
                "input_body_ids": ["A"],
                "expected_affected_body_ids": ["A"],
            },
            {
                "mode": "explicit_ab",
                "input_body_ids": ["A", "B"],
                "expected_affected_body_ids": ["A", "B"],
            },
        ],
        "Unexpected scope cases",
    )
    tolerance = spec["tolerances"]
    require(
        set(tolerance)
        == {"length_mm_absolute", "volume_mm3_absolute", "volume_relative"}
        and all(
            type(value) in (int, float) and math.isfinite(value) and value > 0
            for value in tolerance.values()
        ),
        "Invalid scope-control tolerances",
    )
    intact = expected_body(spec, "B", False)["volume_mm3"]
    perforated = expected_body(spec, "B", True)["volume_mm3"]
    require(
        tolerance["length_mm_absolute"]
        < bodies["A"]["bounds_mm"][0][2] - bodies["B"]["bounds_mm"][1][2]
        and intact - perforated > volume_limit(intact, perforated, tolerance),
        "Comparison tolerances cannot distinguish the controls",
    )


def outline(helper, sketch, bounds, plane_height):
    low, high = bounds
    helper["rectangle"](
        sketch,
        [
            (low[0], low[1], plane_height),
            (high[0], low[1], plane_height),
            (high[0], high[1], plane_height),
            (low[0], high[1], plane_height),
        ],
    )


def create_boss(helper, root, bounds, name):
    adsk = helper["adsk"]
    low, high = bounds
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.name = name + "Profile"
    outline(helper, sketch, bounds, 0)
    require(sketch.profiles.count == 1, "Boss sketch does not own a single profile")
    extrudes = root.features.extrudeFeatures
    entry = extrudes.createInput(
        sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    length = adsk.core.ValueInput.createByString(f"{high[2] - low[2]} mm")
    require(
        entry.setOneSideExtent(
            adsk.fusion.DistanceExtentDefinition.create(length),
            adsk.fusion.ExtentDirections.PositiveExtentDirection,
        ),
        "Fusion refused boss depth",
    )
    if low[2] != 0:
        offset = adsk.core.ValueInput.createByString(f"{low[2]} mm")
        entry.startExtent = adsk.fusion.OffsetStartDefinition.create(offset)
    feature = extrudes.add(entry)
    require(
        feature is not None and feature.bodies.count == 1,
        "Boss does not create one solid",
    )
    feature.name = name
    return feature


def select_profile(helper, sketch, cut, tolerances):
    low, high = cut["profile_bounds_mm"]
    expected = (high[0] - low[0]) * (high[1] - low[1])
    candidates = [
        profile
        for profile in collection(sketch.profiles)
        if abs(profile.areaProperties(helper["ACCURACY"]).area * 100 - expected)
        <= tolerances["length_mm_absolute"] * max(high[0] - low[0], high[1] - low[1])
    ]
    require(len(candidates) == 1, "Cut profile area does not resolve a unique loop")
    return candidates[0]


def author(helper, app, owned, spec, case):
    adsk = helper["adsk"]
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    require(document is not None, "Fusion did not create a new document")
    owned.append(document)
    design = helper["design_of"](document)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    design.fusionUnitsManager.distanceDisplayUnits = (
        adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    )
    root = design.rootComponent
    bosses = {}
    for role in ("A", "B"):
        body = spec["bodies"][role]
        bosses[role] = create_boss(helper, root, body["bounds_mm"], body["producer"])
    require(design.computeAll(), "Fusion refused pre-cut recompute")
    cut = spec["cut"]
    height = cut["profile_bounds_mm"][0][2]
    face = helper["top_face"](bosses["A"].bodies.item(0), "XY", height)
    sketch = root.sketches.add(face)
    sketch.name = cut["sketch"]
    outline(helper, sketch, cut["profile_bounds_mm"], height)
    profile = select_profile(helper, sketch, cut, spec["tolerances"])
    extrudes = root.features.extrudeFeatures
    participants = {role: boss.bodies.item(0) for role, boss in bosses.items()}
    for body in participants.values():
        body.isLightBulbOn = True
        require(body.isVisible, "Both intersected bosses must be visible at authoring")
    entry = extrudes.createInput(
        profile, adsk.fusion.FeatureOperations.CutFeatureOperation
    )
    require(
        entry.setOneSideExtent(
            adsk.fusion.ThroughAllExtentDefinition.create(),
            adsk.fusion.ExtentDirections.NegativeExtentDirection,
        ),
        "Fusion refused the negative through-all extent",
    )
    if case["input_body_ids"] is not None:
        entry.participantBodies = [
            participants[role] for role in case["input_body_ids"]
        ]
    feature = extrudes.add(entry)
    require(feature is not None, "Fusion did not create the through-all cut")
    feature.name = cut["feature"]
    require(design.computeAll(), "Fusion refused authoring recompute")
    return document


def collection(items):
    return tuple(items.item(index) for index in range(items.count))


def resolve_body(helper, design, token):
    matches = design.findEntityByToken(token) or ()
    require(len(matches) == 1, "Body token does not resolve exactly one entity")
    body = helper["adsk"].fusion.BRepBody.cast(matches[0])
    require(
        body is not None and body.isValid and body.isSolid,
        "Resolved entity is not a valid solid",
    )
    return body


def body_row(helper, body):
    require(body.isValid and body.isSolid, "Expected a valid solid body")
    box = body.boundingBox
    props = body.getPhysicalProperties(helper["ACCURACY"])
    row = {
        "bounds_mm": [
            helper["point_mm"](box.minPoint),
            helper["point_mm"](box.maxPoint),
        ],
        "volume_mm3": body.volume * 1000,
        "centroid_mm": helper["point_mm"](props.centerOfMass),
        "face_count": body.faces.count,
        "edge_count": body.edges.count,
        "vertex_count": body.vertices.count,
    }
    require(
        all(math.isfinite(value) for value in (*row["centroid_mm"], row["volume_mm3"]))
        and row["volume_mm3"] > 0,
        "Fusion returned invalid physical properties",
    )
    bounds_pair(row["bounds_mm"])
    return row


def actors(helper, design, spec):
    root = design.rootComponent
    timeline = design.timeline
    require(
        timeline.markerPosition == timeline.count
        and root.occurrences.count == 0
        and design.designType == helper["adsk"].fusion.DesignTypes.ParametricDesignType,
        "Expected one root parametric part at the end of its timeline",
    )
    all_extrusions = collection(root.features.extrudeFeatures)
    expected = {body["producer"] for body in spec["bodies"].values()} | {
        spec["cut"]["feature"]
    }
    by_name = {item.name: item for item in all_extrusions}
    require(
        len(all_extrusions) == len(expected) and set(by_name) == expected,
        "Unexpected extrusion identities",
    )
    bosses = {role: by_name[body["producer"]] for role, body in spec["bodies"].items()}
    cut = by_name[spec["cut"]["feature"]]
    sketches = [
        item for item in collection(root.sketches) if item.name == spec["cut"]["sketch"]
    ]
    require(len(sketches) == 1, "Cut sketch ownership does not resolve uniquely")
    (sketch,) = sketches
    kinds = helper["adsk"].fusion.FeatureOperations
    require(
        all(boss.operation == kinds.NewBodyFeatureOperation for boss in bosses.values())
        and cut.operation == kinds.CutFeatureOperation
        and bosses["A"].timelineObject.index
        < bosses["B"].timelineObject.index
        < sketch.timelineObject.index
        < cut.timelineObject.index,
        "Unexpected boss, sketch or Cut operation order",
    )
    for item in (*bosses.values(), sketch, cut):
        marker = item.timelineObject
        require(
            not marker.isSuppressed
            and not marker.isRolledBack
            and int(marker.healthState) == 0,
            f"Unhealthy saved timeline item: {item.name}",
        )
    return bosses, sketch, cut


def producer_row(feature):
    return {
        "name": feature.name,
        "native_id": feature.timelineObject.index,
        "identity_kind": "fusion_timeline_index",
    }


def verify_roster(bodies, current):
    require(len(current) == len(bodies), "Unexpected live body count")
    require(
        all(
            sum(body == candidate for candidate in current) == 1
            for body in bodies.values()
        )
        and all(
            sum(body == candidate for body in bodies.values()) == 1
            for candidate in current
        ),
        "Body ownership is not bijective",
    )


def cut_before(helper, fresh, design, spec, actors_value, pre_tokens, before_cut):
    bosses, sketch, cut = actors_value
    bodies = {}
    for role, boss in bosses.items():
        require(
            boss.bodies.count == 1, "Historical boss does not resolve exactly one body"
        )
        native = boss.bodies.item(0)
        body = resolve_body(helper, design, native.entityToken)
        bodies[role] = body
        pre_tokens[role] = native.entityToken
        before_cut[role] = {**body_row(helper, body), "producer": producer_row(boss)}
    verify_roster(bodies, collection(design.rootComponent.bRepBodies))
    adsk = helper["adsk"]
    extent = adsk.fusion.ThroughAllExtentDefinition.cast(cut.extentOne)
    require(
        extent is not None and not cut.hasTwoExtents, "Cut is not one-sided through-all"
    )
    require(not extent.isPositiveDirection, "Saved Cut points the wrong way")
    start = cut.startExtent
    require(
        start is not None
        and start.objectType == adsk.fusion.ProfilePlaneStartDefinition.classType(),
        "Saved Cut does not start on its profile plane",
    )
    profile = adsk.fusion.Profile.cast(cut.profile)
    require(
        profile is not None and profile.parentSketch == sketch,
        "Saved Cut profile does not reach its support sketch",
    )
    expected_profile = select_profile(helper, sketch, spec["cut"], spec["tolerances"])
    require(profile == expected_profile, "Saved Cut does not use the witnessed loop")
    support = fresh["cut_support"](helper, design, sketch, bosses["A"])
    require(support["status"] == "verified", "Cut support did not reach A's end cap")
    normal = xyz(sketch.xDirection.crossProduct(sketch.yDirection))
    require(
        near(normal, support["normal_world"], 1e-9)
        and near(
            tuple(-value for value in normal), spec["cut"]["direction_world"], 1e-9
        )
        and abs(support["signed_offset_mm"] - spec["cut"]["profile_bounds_mm"][0][2])
        <= spec["tolerances"]["length_mm_absolute"],
        "Saved Cut normal or supporting plane disagrees with the control",
    )
    raw_participants = cut.participantBodies
    require(
        raw_participants is not None, "Fusion did not expose saved Cut participants"
    )
    participants = []
    for native in raw_participants:
        candidate = resolve_body(helper, design, native.entityToken)
        matches = [role for role, body in bodies.items() if candidate == body]
        require(len(matches) == 1, "Saved participant has no unique boss producer")
        participants.append(matches[0])
    require(
        participants and len(participants) == len(set(participants)),
        "Fusion participant roster is empty or repeats an identity",
    )
    return {
        "status": "verified",
        "end_condition": "through_all",
        "direction_world": [-value for value in normal],
        "depth_mm": None,
        "target_body_ids": sorted(participants),
        "observed_policy": None,
        "native": {
            "operation": int(cut.operation),
            "extent_type": extent.objectType,
            "start_type": start.objectType,
            "is_positive_direction": bool(extent.isPositiveDirection),
            "has_two_extents": bool(cut.hasTwoExtents),
            "participant_marker": design.timeline.markerPosition,
            "participant_count": len(participants),
            "support_cap": support,
        },
    }


def expected_body(spec, role, affected):
    low, high = spec["bodies"][role]["bounds_mm"]
    cut_low, cut_high = spec["cut"]["profile_bounds_mm"]
    thickness = high[2] - low[2]
    start_volume = (high[0] - low[0]) * (high[1] - low[1]) * thickness
    removed = (
        (cut_high[0] - cut_low[0]) * (cut_high[1] - cut_low[1]) * thickness
        if affected
        else 0
    )
    remaining = start_volume - removed
    center = [(value + other) / 2 for value, other in zip(low, high)]
    cutter = [(cut_low[0] + cut_high[0]) / 2, (cut_low[1] + cut_high[1]) / 2, center[2]]
    return {
        "bounds_mm": [low, high],
        "volume_mm3": remaining,
        "centroid_mm": [
            origin - (cut_center - origin) * removed / remaining
            for origin, cut_center in zip(center, cutter)
        ],
        "face_count": 10 if affected else 6,
        "edge_count": 24 if affected else 12,
        "vertex_count": 16 if affected else 8,
    }


def compare_body(first, second, tolerance, label):
    limit = tolerance["length_mm_absolute"]
    require(
        all(
            near(left, right, limit)
            for left, right in zip(first["bounds_mm"], second["bounds_mm"])
        )
        and near(first["centroid_mm"], second["centroid_mm"], limit)
        and abs(first["volume_mm3"] - second["volume_mm3"])
        <= volume_limit(first["volume_mm3"], second["volume_mm3"], tolerance)
        and all(
            first[field] == second[field]
            for field in ("face_count", "edge_count", "vertex_count")
        ),
        f"Body measurements disagree: {label}",
    )


# the first sample precedes any rollback so it measures the actual reopened result
def observe(helper, fresh, document, spec, case, stage, before_cut):
    design = helper["design_of"](document)
    assembly = actors(helper, design, spec)
    bosses, _, cut = assembly
    root = design.rootComponent
    samples = [
        (body.entityToken, body_row(helper, body))
        for body in collection(root.bRepBodies)
    ]
    stage["unattributed_bodies_before_rollback"] = [row for _, row in samples]
    require(len(samples) == 2, "Expected two solids before any rollback")
    pre_tokens = {}
    cut_probe = fresh["measure_at_marker"](
        design.timeline,
        cut.timelineObject,
        True,
        lambda: cut_before(
            helper, fresh, design, spec, assembly, pre_tokens, before_cut
        ),
    )
    stage["cut"] = cut_probe
    require(
        cut_probe["status"] == "verified",
        "Saved through-all relationships are unresolved",
    )
    affected = case["expected_affected_body_ids"]
    require(
        cut_probe["target_body_ids"] == affected,
        "Saved participant roster disagrees with the control",
    )
    current = {
        role: resolve_body(helper, design, token) for role, token in pre_tokens.items()
    }
    verify_roster(current, collection(root.bRepBodies))
    restored_samples = [
        (resolve_body(helper, design, token), row) for token, row in samples
    ]
    rows = {}
    for role, body in current.items():
        matching = [row for candidate, row in restored_samples if candidate == body]
        require(
            len(matching) == 1, "Initial solid sample has no unique historical producer"
        )
        (sample,) = matching
        compare_body(
            sample,
            body_row(helper, body),
            spec["tolerances"],
            role + " after marker restore",
        )
        rows[role] = {**sample, "producer": producer_row(bosses[role])}
        compare_body(
            before_cut[role],
            expected_body(spec, role, False),
            spec["tolerances"],
            role + " before Cut",
        )
        compare_body(
            sample,
            expected_body(spec, role, role in affected),
            spec["tolerances"],
            role + " after Cut",
        )
    stage["bodies"] = rows
    stage.pop("unattributed_bodies_before_rollback")
