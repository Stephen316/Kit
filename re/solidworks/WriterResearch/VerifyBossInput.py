from argparse import ArgumentParser
from hashlib import sha256
import json

from VerifyConfigRoot import ROOT, require

from PairedCaptureIntake import GitSnapshot, recipe_roster
from RectanglePairEvidence import (
    REVISION,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    capture,
    load_public,
)
from RectanglePairSketch import parameter_mm, same, unique, xyz
from convert.Commands.CheckPortable import CheckPortable
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureExtrude import ExtrudeFeature


# public discovery projections retain their original portability refusals
def portable_refusal(document):
    try:
        CheckPortable(document)
    except ValueError as error:
        return str(error).split(" ", 1)[0]
    raise ValueError(
        "paired discovery projection must retain its qualification boundary"
    )


# cross-check physical width, height and signed depth without reclassifying parameter roles
def profile_facts(document):
    (sketch,) = document.sketches
    frame = unique(
        (
            plane.transform
            for plane in document.support_planes
            if plane.id == sketch.support_plane_id
        ),
        "paired principal datum",
    )
    boss = unique(
        (
            feature
            for feature in document.feature_timeline
            if feature.kind == "extrusion"
        ),
        "paired single boss",
    )
    parameters = {item.id: item for item in document.parameters}
    width, height = (
        parameter_mm(
            unique((item for item in parameters.values() if item.name == name), name)
        )
        for name in ("width_mm", "height_mm")
    )
    definition = boss.definition
    if isinstance(definition, DistanceExtrude):
        depth = parameter_mm(parameters[definition.AlongParameterId])
    elif isinstance(definition, ExtrudeFeature):
        depth = parameter_mm(
            unique(
                (
                    parameters[identity]
                    for identity in boss.parameter_ids
                    if parameters[identity].name == "depth_mm"
                ),
                "SOLIDWORKS depth driver",
            )
        )
        if definition.reversed:
            depth = -depth
    else:
        raise ValueError("paired boss lost its typed end")
    return (xyz(frame.z_axis), width, height, depth)


# paired receipts are read-only evidence and do not build an authored candidate
def paired_rows():
    snapshot = GitSnapshot(ROOT)
    source = snapshot.blob(REVISION, SPECIFICATION)
    require(sha256(source).hexdigest() == SPECIFICATION_SHA256, "pinned paired recipe")
    spec = snapshot.parse_document(source, SPECIFICATION)
    recipe = recipe_roster(spec)["P03"]
    tolerance = spec["comparison_tolerances"]
    fusion, fusion_assets, _ = capture(snapshot, recipe, "fusion", spec)
    sw, sw_assets, _ = capture(snapshot, recipe, "solidworks", spec)
    require(
        fusion["canonical_recipe_sha256"] == sw["canonical_recipe_sha256"]
        and fusion_assets.keys() == sw_assets.keys()
        and len(fusion_assets) == 8,
        "same eight P03 discovery variants",
    )
    rows = []
    for variant in sorted(sw_assets):
        fusion_asset, sw_asset = fusion_assets[variant], sw_assets[variant]
        _, fusion_doc = load_public(snapshot, fusion_asset, "fusion")
        _, sw_doc = load_public(snapshot, sw_asset, "solidworks")
        left, right = profile_facts(fusion_doc), profile_facts(sw_doc)
        same(
            left[0],
            right[0],
            tolerance["angle_rad_absolute"],
            f"{variant} principal normal",
        )
        same(
            left[1:],
            right[1:],
            tolerance["length_mm_absolute"],
            f"{variant} sizes and signed depth",
        )
        refusals = (portable_refusal(fusion_doc), portable_refusal(sw_doc))
        require(
            refusals == ("RetainedPayload", "NativeFeature"),
            "current paired admission gates",
        )
        rows.append(
            (variant, fusion_asset["sha256"], sw_asset["sha256"], right, refusals)
        )
    return rows


def report(check_projection):
    rows = paired_rows()
    cases = []
    if check_projection:
        from BossGraphCases import hosted_cases

        cases = hosted_cases()
    return {
        "capture_revision": REVISION,
        "captures": {row[2]: row[1] for row in rows},
        "paired_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "authored_cases": cases,
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Inspect the paired portable P03 graph boundary"
    )
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
