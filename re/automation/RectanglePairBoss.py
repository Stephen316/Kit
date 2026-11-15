"""Check both normalized blind boss extents against typed archives and native readbacks."""

from struct import unpack_from

from FusionBossDirectionEvidence import compare_solidworks_direction
from PairedCaptureIntake import require
from RectanglePairSketch import parameter_mm, same, unique, xyz
from convert.adapters.solidworks.container.Archive import KObjectRefKind, ReadTag
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.resolved.RectanglePart import ReadRectPart
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureExtrude import ExtrudeFeature


def find_boss(document, sketch):
    boss = unique(
        (row for row in document.feature_timeline if row.kind == "extrusion"),
        "public boss",
    )
    require(
        boss.name == "BlindBoss"
        and boss.sketch_id == sketch.id
        and not boss.suppressed
        and boss.provenance is not None,
        "public boss does not own the verified rectangle",
    )
    (loop,) = sketch.closed_profile_entity_ids
    require(len(loop) == len(set(loop)) == 4, "boss profile requires four owned sides")
    return boss, loop


def fusion_boss(document, sketch, frame, proof, tolerances):
    boss, loop = find_boss(document, sketch)
    definition = boss.definition
    require(
        isinstance(definition, DistanceExtrude)
        and definition.SideMode == "one_sided"
        and definition.AgainstParameterId is None
        and definition.StartOffsetId is None
        and boss.operation == "create",
        "public Fusion boss end or operation is unsupported",
    )
    profile = proof["boss_profile"]
    native = profile["selection"]
    (native_loop,) = native["loops"]
    members = tuple(
        f"fusion-sketch-entity-{row['entity_id']}"
        for row in native_loop["curve_references"]
    )
    require(
        boss.attributes["fusion.profile_entity_ids"] == loop
        and boss.attributes["fusion.profile_native_members"] == members
        and set(members) == set(loop)
        and boss.attributes["fusion.profile_descriptor_id"]
        == native["descriptor_object_id"]
        and boss.attributes["fusion.profile_loop_object_id"]
        == native["loop_definition_object_id"]
        and boss.attributes["fusion.profile_selection_proxy_id"]
        == profile["profile_proxy"]["object_id"],
        "public Fusion selection differs from saved proxy and loop",
    )
    controls = proof["boss_controls"]
    expected = controls["signed_along_distance"]
    parameter = unique(
        (row for row in document.parameters if row.id == definition.AlongParameterId),
        "Fusion authored AlongDistance",
    )
    require(
        parameter.name == expected["parameter_name"]
        and parameter.owner_id == boss.id
        and parameter.id == f"fusion-parameter-{expected['parameter_object_id']}"
        and boss.attributes["fusion.extrude.along_binding_object_id"]
        == expected["binding_object_id"],
        "public Fusion boss uses another distance parameter",
    )
    signed = parameter_mm(parameter)
    tolerance = tolerances["length_mm_absolute"]
    require(
        abs(signed - expected["raw_value_cm"] * 10) <= tolerance,
        "public Fusion signed depth differs from the archive",
    )
    direction = xyz(definition.Direction)
    angle = tolerances["angle_rad_absolute"]
    same(
        direction,
        controls["controls"]["extent"]["stored_direction_vector"],
        angle,
        "Fusion saved direction differs",
    )
    same(
        direction,
        xyz(frame.z_axis),
        angle,
        "Fusion boss direction differs from the profile normal",
    )
    require(
        boss.attributes["fusion.extrude.start_kind"] == "profile_plane"
        and boss.attributes["fusion.extrude.end_kind"] == "distance",
        "public Fusion boss start or end differs from the archive",
    )
    return {
        "step_id": boss.id,
        "operation": str(boss.operation),
        "selected_entities": loop,
        "native_profile_proxy": profile["profile_proxy"]["object_id"],
        "native_profile_descriptor": native["descriptor_object_id"],
        "distance_parameter": parameter.id,
        "native_distance_binding": expected["binding_object_id"],
        "signed_depth_mm": signed,
        "direction": direction,
        "displacement_mm": tuple(signed * value for value in direction),
    }


def solidworks_boss(document, sketch, frame, raw, tolerances):
    boss, loop = find_boss(document, sketch)
    definition = boss.definition
    require(
        isinstance(definition, ExtrudeFeature)
        and definition.length is not None
        and definition.end_condition == "blind"
        and boss.operation == "join"
        and not definition.symmetric
        and definition.second_length is None,
        "public SOLIDWORKS boss end or operation is unsupported",
    )
    archive = SldprtArchive.from_bytes(raw)
    stream = "Contents/Config-0-ResolvedFeatures"
    resolved = archive.require(stream)
    saved = ReadRectPart(archive.require("Contents/Config-0"), resolved, 19000)
    operation = saved.Boss
    require(
        operation is not None
        and operation["profile_object"] == saved.Profile.ObjectIndex
        and operation["native_feature_id"] == boss.attributes["native_object_id"]
        and boss.attributes["profile_native_id"] == saved.Profile.FeatureId
        and sketch.attributes["support_plane_native_id"] == saved.Reference.FeatureId,
        "SOLIDWORKS saved operation points to a different profile",
    )
    spans = {item.record_kind: item for item in boss.provenance.spans}
    reference = spans["operation-profile-reference"]
    require(
        (reference.stream, reference.offset, reference.length)
        == (stream, operation["profile_ref_offset"], 2),
        "public SOLIDWORKS profile source span differs",
    )
    tag = ReadTag(resolved, reference.offset)
    require(
        (tag.kind, tag.index) == (KObjectRefKind, saved.Profile.ObjectIndex),
        "SOLIDWORKS public profile span does not identify the saved object",
    )
    actual = operation["depth_display"]["dimension"]
    scalar = spans["extrusion-depth-scalar"]
    parameter = unique(
        (
            row
            for row in document.parameters
            if row.id in boss.parameter_ids and row.name == actual["parameter_name"]
        ),
        "SOLIDWORKS authored depth parameter",
    )
    require(
        (scalar.stream, scalar.offset, scalar.length)
        == (stream, actual["value_offset"], 8)
        and unpack_from("<d", resolved, scalar.offset) == (actual["metres"],)
        and definition.length.unit == "mm"
        and parameter.owner_id == boss.id
        and parameter.provenance is not None
        and [
            (item.stream, item.offset, item.length, item.record_kind)
            for item in parameter.provenance.spans
        ]
        == [(scalar.stream, scalar.offset, scalar.length, "dimension-scalar")]
        and parameter_mm(parameter) == definition.length.value
        and abs(definition.length.value - 1000 * actual["metres"])
        <= tolerances["length_mm_absolute"]
        and definition.reversed == (operation["end_specification"]["direction"] == 1),
        "public SOLIDWORKS depth or direction differs from its saved typed record",
    )
    direction = (
        xyz(frame.z_axis) if definition.direction is None else xyz(definition.direction)
    )
    same(
        direction,
        xyz(frame.z_axis),
        tolerances["angle_rad_absolute"],
        "SOLIDWORKS boss direction differs from the profile normal",
    )
    signed = definition.length.value * (-1 if definition.reversed else 1)
    return {
        "step_id": boss.id,
        "operation": str(boss.operation),
        "selected_entities": loop,
        "native_profile_object": saved.Profile.ObjectIndex,
        "native_profile_ref_offset": reference.offset,
        "distance_parameter": parameter.id,
        "native_distance_scalar_offset": scalar.offset,
        "signed_depth_mm": signed,
        "direction": direction,
        "displacement_mm": tuple(signed * value for value in direction),
    }


def compare_boss(
    fusion, solidworks, fusion_observed, sw_observed, proof, links, tolerances
):
    independent = compare_solidworks_direction(
        sw_observed, fusion_observed, proof["boss_controls"], tolerances
    )
    require(
        set(fusion["selected_entities"]) == set(links)
        and {links[edge] for edge in fusion["selected_entities"]}
        == set(solidworks["selected_entities"]),
        "public bosses select different perimeter members",
    )
    tolerance = tolerances["length_mm_absolute"]
    same(
        fusion["displacement_mm"],
        solidworks["displacement_mm"],
        tolerance,
        "public boss signed extents differ",
    )
    same(
        solidworks["displacement_mm"],
        independent["solidworks_displacement_from_section_and_mass_center_mm"],
        tolerance,
        "public boss differs from independently measured SOLIDWORKS displacement",
    )
    same(
        fusion["displacement_mm"],
        independent["fusion_displacement_from_saved_axis_and_depth_mm"],
        tolerance,
        "public boss differs from independently witnessed Fusion direction",
    )
    return {
        "status": "equal",
        "fusion": fusion,
        "solidworks": solidworks,
        "historical_evidence": independent,
        "operation_label": {
            "status": "different",
            "fusion": fusion["operation"],
            "solidworks": solidworks["operation"],
        },
    }
