# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import PurePosixPath
from struct import unpack_from

from FusionCutExtentEvidence import (
    EXTRUDE_CLASS,
    REVISION,
    ROOT,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    design_members,
    inspect_archive,
)
from FusionCutSketchEvidence import historical_observations
from P04FinalBodyEvidence import captures as cut_captures
from PairedCaptureIntake import GitSnapshot, recipe_roster, require, sha256
from RectanglePairEvidence import capture
from SolidWorksScopeArchive import (
    CONTROL_ARCHIVE,
    CONTROL_RECEIPT,
    GENERATION,
    RESOLVED,
    SOURCE_FOLDER,
    SOURCE_REVISION,
    SOURCE_SHA256,
)
from decode_basics import attach_parameters, named_features
from decode_parameters import decode_stream
from fusion_metadata import design_records

from convert.adapters.solidworks.config.CutConfig import ReadCutConfig
from convert.adapters.solidworks.container.Archive import ContainerMo, ReadTag
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.resolved.RectanglePart import ReadRectPart
from convert.adapters.solidworks.resolved.cut.CutLinks import ReadCutLinks
from convert.adapters.solidworks.resolved.cut.CutProof import ReadCutProof

FORMATS = {"fusion": "fusion.f3d", "solidworks": "solidworks.sldprt"}
CONFOUNDS = ("width_mm", "height_mm")


def capture_spec(snapshot):
    content = snapshot.blob(REVISION, SPECIFICATION)
    require(sha256(content) == SPECIFICATION_SHA256, "inference recipe pin differs")
    return snapshot.parse_document(content, SPECIFICATION)


def native_bytes(snapshot, asset):
    data = snapshot.blob(REVISION, asset["path"])
    require(
        len(data) == asset["size_bytes"] and sha256(data) == asset["sha256"],
        "inference archive differs from capture pin",
    )
    return data


def observations(snapshot, evidence):
    pin = evidence["measurements"]
    content = snapshot.blob(REVISION, pin["path"])
    require(sha256(content) == pin["sha256"], "inference measurements differ from pin")
    data = snapshot.parse_document(content, pin["path"])
    if evidence["application"] == "fusion":
        return historical_observations(evidence, data)
    require(
        data["authoring_process_id"] != data["reopen_process_id"],
        "inference requires independent SOLIDWORKS reopen observations",
    )
    files = data["observations"]["reopened_files"]
    result = {}
    for asset in evidence["native_files"]:
        sample = files[PurePosixPath(asset["path"]).name]
        require(
            sample["open_status"] == {"errors": 0, "warnings": 0},
            "inference source failed to reopen cleanly",
        )
        result[asset["variant"]] = ("separate_process_reopen", sample)
    return result


def unique(items, explanation):
    choices = list(items)
    require(len(choices) == 1, explanation)
    return choices[0]


def measured_dimensions(entries, value_key, units_per_mm):
    return {
        name: unique(
            (row[value_key] for row in entries if row["name"] == name),
            f"inference requires one independently observed {name}",
        )
        / units_per_mm
        for name in CONFOUNDS
    }


def measured_fusion_boss(observation):
    parameters = observation["parameters"]
    depth = unique(
        (row["value_internal"] for row in parameters if row["name"] == "depth_mm"),
        "inference requires one observed Fusion boss depth",
    )
    return depth * 10, measured_dimensions(parameters, "value_internal", 0.1)


def observed_feature(observation, name):
    feature = unique(
        (row for row in observation["feature_tree"] if row["name"] == name),
        f"inference requires one observed SOLIDWORKS {name}",
    )
    require(
        not feature["suppressed"]
        and feature["error_code"] == 0
        and not feature["warning"],
        f"inference source reports a suppressed or unhealthy {name}",
    )
    return feature


def measured_solidworks_boss(observation):
    boss = observed_feature(observation, "BlindBoss")["operation"]
    drawing = observed_feature(observation, "RectangleSketch")
    reverse = boss["reverse_direction"]
    require(
        boss["end_condition"] == 0
        and boss["both_directions"] is False
        and type(reverse) is bool
        and boss["depth_m"] > 0,
        "inference source is outside the one-sided blind boss controls",
    )
    return (
        (-1000 if reverse else 1000) * boss["depth_m"],
        measured_dimensions(drawing["dimensions"], "system_value", 0.001),
    )


def fusion_boss_stream(data):
    streams, sources = design_members(data)
    bulk = streams["BulkStream.dat"]
    records, _ = design_records(bulk, streams["MetaStream.dat"])
    features = named_features(bulk, records)
    parameters, rejected = decode_stream(bulk, records)
    require(
        not rejected and not attach_parameters(bulk, records, features, parameters),
        "Fusion inference could not bind the indexed parameters",
    )
    boss = unique(
        (
            row
            for row in features
            if row["kind"] == "Extrude" and row["name"] == "BlindBoss"
        ),
        "Fusion inference could not identify a unique boss owner",
    )
    owner = unique(
        (
            row
            for row in records
            if row.is_primary
            and row.class_guid == EXTRUDE_CLASS
            and row.start == boss["record_offset"]
        ),
        "Fusion boss owner lacks one typed primary record",
    )
    binding = unique(
        (row for row in boss["parameters"] if row["role"] == "AlongDistance"),
        "Fusion boss AlongDistance does not have one owned binding",
    )
    value_site = binding["value_offset"]
    record = unique(
        (
            row
            for row in records
            if row.is_primary
            and row.object_id == binding["parameter_object_id"]
            and row.body <= value_site < row.end
        ),
        "Fusion boss length lacks one primary model parameter record",
    )
    start = record.end - 32
    require(
        start >= record.body and start <= value_site <= record.end - 8,
        "Fusion inference parameter suffix cannot be aligned",
    )
    return (
        bulk,
        sources["BulkStream.dat"]["path"],
        start,
        32,
        {
            "alignment": "indexed numeric parameter record end",
            "owner_record": owner.object_id,
            "parameter_record": record.object_id,
            "binding_record": binding["binding_object_id"],
            "typed_scalar_offset": value_site,
            "companion_stream_sha256": sources["MetaStream.dat"]["sha256"],
        },
    )


def solidworks_streams(data):
    archive = SldprtArchive.from_bytes(data)
    require(
        ContainerMo(archive.streams) == GENERATION,
        "SOLIDWORKS inference expected the pinned archive generation",
    )
    return archive.require("Contents/Config-0"), archive.require(RESOLVED)


def solidworks_boss_stream(data):
    config, resolved = solidworks_streams(data)
    part = ReadRectPart(config, resolved, GENERATION)
    boss = part.Boss
    require(
        boss is not None
        and boss["name"] == "BlindBoss"
        and boss["profile_object"] == part.Profile.ObjectIndex,
        "SOLIDWORKS inference requires the reached boss and owned profile",
    )
    parameter = boss["depth_display"]["dimension"]
    start, end = parameter["offset"], parameter["end"]
    require(
        start <= parameter["value_offset"] <= end - 8,
        "SOLIDWORKS depth extends outside the typed dimension",
    )
    return (
        resolved,
        RESOLVED,
        start,
        end - start,
        {
            "alignment": "owned distance dimension record start",
            "owner_record": boss["native_feature_id"],
            "parameter_record": parameter["parameter_object"],
            "typed_scalar_offset": parameter["value_offset"],
            "separate_direction": boss["end_specification"]["direction"],
            "companion_stream_sha256": sha256(config),
        },
    )


def archive_side(snapshot, specification, recipe, application):
    evidence, assets, _ = capture(snapshot, recipe, application, specification)
    measured = observations(snapshot, evidence)
    measure, extract = {
        "fusion": (measured_fusion_boss, fusion_boss_stream),
        "solidworks": (measured_solidworks_boss, solidworks_boss_stream),
    }[application]
    provenance = {
        "capture_revision": REVISION,
        "specification_sha256": SPECIFICATION_SHA256,
        "recipe_sha256": evidence["canonical_recipe_sha256"],
        "receipt": evidence["receipt"],
        "measurements": evidence["measurements"],
        "application_build": evidence["application_build"],
        "qualification_blockers": evidence["qualification_blockers"],
        "inputs": {},
    }
    samples, streams, native_sources = [], {}, {}
    for variant, asset in sorted(assets.items()):
        data = native_bytes(snapshot, asset)
        contents, stream, start, length, source = extract(data)
        phase, observation = measured[variant]
        value, controls = measure(observation)
        role = f"p03-{application}-{variant}"
        native_sources[asset["sha256"]] = (FORMATS[application], data)
        streams[role] = contents
        provenance["inputs"][variant] = {
            **source,
            "archive_path": asset["path"],
            "archive_sha256": asset["sha256"],
            "archive_git_blob": asset["git_blob"],
            "stream_sha256": sha256(contents),
            "historical_phase": phase,
        }
        samples.append(
            {
                "id": variant,
                "lineage": f"{recipe['family']}.{application}",
                "sha256": asset["sha256"],
                "stream": stream,
                "start": start,
                "length": length,
                "value": value,
                "controls": controls,
                "role": role,
                "split": (
                    "challenge" if variant == "direction-negative" else "discovery"
                ),
            }
        )
    encodings = [
        {"type": kind, "endian": endian, "unit": unit, "scale": scale, "offset": 0}
        for kind in ("u8", "i8", "u16", "i16", "u32", "i32", "u64", "i64", "f32", "f64")
        for endian in ("little", "big")
        for unit, scale in (("mm", 1), ("cm", 0.1), ("m", 0.001), ("in", 1 / 25.4))
    ]
    return (
        {
            "inference_version": 1,
            "scope": f"p03-blind-boss.{application}",
            "quantity": "signed-depth-mm",
            "provenance": provenance,
            "encodings": encodings,
            "tolerance": specification["comparison_tolerances"]["length_mm_absolute"],
            "confounds": list(CONFOUNDS),
            "observations": samples,
        },
        streams,
        native_sources,
    )


def archive_cases():
    snapshot = GitSnapshot(ROOT)
    specification = capture_spec(snapshot)
    recipe = recipe_roster(specification)["P03"]
    require(recipe["split"] == "discovery", "P03 inference split differs")
    for application in FORMATS:
        yield archive_side(snapshot, specification, recipe, application)


def fusion_cut_sites(data, through_all):
    proof = inspect_archive(data)
    cut = proof["extrusions"]["Cut"]
    condition = cut["controls"]["extent"]["side_one"]["condition"]
    depths = cut["owned_along_distance"]
    require(
        (
            (not depths and condition == "ThroughAll")
            if through_all
            else (len(depths) == 1 and condition == "Distance")
        ),
        "Fusion cut does not distinguish blind depth from through-all",
    )
    parameter = None if through_all else depths[0]
    return {
        "stream": proof["design_members"]["BulkStream.dat"],
        "feature_span": cut["record"],
        "end_condition": condition,
        "depth_parameter": parameter,
        "end_reference_records": cut["end_reference_records"],
        "saved_targets": proof["selection_routes"]["cut_body_list_selection"],
    }


def solidworks_cut_sites(data, through_all):
    config, stream = solidworks_streams(data)
    configuration = ReadCutConfig(config, GENERATION)
    proof = ReadCutProof(ReadCutLinks(stream, configuration), configuration)
    operation = proof.Operation
    end = operation["end_specification"]
    display = end["depth_display"]
    condition = end["conditions"][0]
    require(
        (condition, display is None) == (int(through_all), through_all),
        "SOLIDWORKS cut does not distinguish blind depth from through-all",
    )
    selector = ReadTag(stream, end["depth_selector_offset"])
    body = operation["solid_body"]
    scope_offset = body["end"]
    (scope_word,) = unpack_from("<i", stream, scope_offset)
    return {
        "stream": {
            "path": RESOLVED,
            "sha256": sha256(stream),
            "size_bytes": len(stream),
        },
        "feature_span": {"start": operation["offset"], "end": end["end"]},
        "end_condition": condition,
        "depth_parameter": None if display is None else display["dimension"],
        "depth_selector": {
            "start": end["depth_selector_offset"],
            "length": selector.size,
            "kind": selector.kind,
        },
        "saved_scope": {
            "producer_id": proof.Links.BossValue["native_feature_id"],
            "body_id": body["body_id"],
            "scope_word": scope_word,
            "scope_word_span": {"start": scope_offset, "length": 4},
        },
    }


def cut_contrasts(snapshot, evidence):
    application = evidence["application"]
    assets = {asset["variant"]: asset for asset in evidence["native_files"]}
    measured = observations(snapshot, evidence)
    contrast = {}
    for variant in ("baseline-a", "termination-through-all"):
        asset = assets[variant]
        data = native_bytes(snapshot, asset)
        through_all = variant == "termination-through-all"
        phase, observation = measured[variant]
        if application == "fusion":
            sites = fusion_cut_sites(data, through_all)
            body = unique(
                observation["bodies"], "P04 Fusion capture must have one body"
            )
            native_body = {key: body[key] for key in ("volume_mm3", "bounding_box_mm")}
        else:
            require(observation["body_count"] == 1, "P04 SOLIDWORKS body count differs")
            sites = solidworks_cut_sites(data, through_all)
            native_body = {"volume_mm3": observation["volume_mm3"]}
        contrast[variant] = {
            "archive": asset,
            "historical_phase": phase,
            "body_observation": native_body,
            **sites,
        }
    require(
        contrast["baseline-a"]["body_observation"]["volume_mm3"]
        > contrast["termination-through-all"]["body_observation"]["volume_mm3"],
        "P04 independent control does not distinguish termination by volume",
    )
    return {
        "receipt": evidence["receipt"],
        "measurements": evidence["measurements"],
        "application_build": evidence["application_build"],
        "controls": contrast,
    }


def archive_gaps():
    snapshot, specification, fusion, solidworks = cut_captures()
    recipe = recipe_roster(specification)["P04"]
    require(
        recipe["split"] == fusion["split"] == solidworks["split"] == "discovery"
        and solidworks["receipt"]["sha256"] == CONTROL_RECEIPT,
        "P04 inference contrast does not match discovery receipt",
    )
    apps = {
        evidence["application"]: cut_contrasts(snapshot, evidence)
        for evidence in (fusion, solidworks)
    }
    native_sources = {
        asset["sha256"]: (FORMATS[app], native_bytes(snapshot, asset))
        for app, proof in apps.items()
        for asset in (item["archive"] for item in proof["controls"].values())
    }
    sw_control = apps["solidworks"]["controls"]["termination-through-all"]
    require(
        sw_control["archive"]["sha256"] == CONTROL_ARCHIVE
        and sw_control["saved_scope"]["scope_word"] == 1,
        "SOLIDWORKS through-all scope contrast differs from its pinned proof",
    )
    grid_path = f"{SOURCE_FOLDER}/ScopeControlSpec.json"
    grid = snapshot.blob(SOURCE_REVISION, grid_path)
    require(
        sha256(grid) == SOURCE_SHA256["ScopeControlSpec.json"], "scope grid pin differs"
    )
    gaps = [
        {
            "inference_version": 1,
            "scope": "p04-cut-termination",
            "recipe_family": recipe["family"],
            "capture_revision": REVISION,
            "status": "refuted",
            "hypothesis": "Every paired Cut owns the same blind depth field",
            "affected_archives": {
                pin: source_format for pin, (source_format, _) in native_sources.items()
            },
            "counterexamples": apps,
        },
        {
            "inference_version": 1,
            "scope": "p04-through-all-body-selection",
            "recipe_family": recipe["family"],
            "capture_revision": REVISION,
            "status": "needs-distinguishing-evidence",
            "hypothesis": "A saved target list identifies automatic versus explicit selection",
            "reason": "One saved target is compatible with both policies on a one-body model",
            "affected_archives": {
                proof["controls"]["termination-through-all"]["archive"][
                    "sha256"
                ]: FORMATS[app]
                for app, proof in apps.items()
            },
            "requested_grid": {
                "specification": grid_path,
                "revision": SOURCE_REVISION,
                "sha256": sha256(grid),
                "cases": snapshot.parse_document(grid, grid_path)["cases"],
            },
        },
    ]
    return gaps, native_sources
