from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import json
from math import dist, isclose

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require

from BossBridge import (
    BossIds,
    BossPose,
    BossWire,
    ProfileWire,
    SizePose,
    BindBossWriter,
)
from BossGraphCases import authored_case
from BossInput import ProjectBoss
from CmgrExternal import ExternalFile
from CmgrInherited import ArchiveFeature
from Display.Compose import DisplayDraft
from DisplayMasks import DisplayPrefs
from HeaderLogs import ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from HeaderTail import KFrameTolerance, ReadHeaderTail
from RectangleRegion import SketchRegionState
from RectangleTrim import RectTrimState, TrimMember
from VerifyBossOpen import open_boss, read_atom, verify_measured
from VerifyModelHeader import measured_bounds
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Cmgr import Stamp
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.BossEntry import ReadRectBoss
from convert.adapters.solidworks.Resolved.ContourSurf import KTrimTypes
from interchange.geometry.Models.VectorSpace import SpaceVector


# allocate a fresh independent target state for an authored neutral model
def wire_state():
    draft = DisplayDraft(
        Preferences=DisplayPrefs(
            design_intent=True,
            inward_tolerance_rounding=False,
            remove_zero=False,
            uppercase_dimension=False,
        ),
        Alignment=(1, 1),
        Standard=4,
        ExtendLeader=True,
        SplitDual=False,
        ArrowHead=0,
        Precision=2,
        AltPrecision=2,
    )
    file = ExternalFile("", "Ordinary proof", 135, 0, "Default")
    path = (4, 3, 2, 1)
    trim = RectTrimState(
        111,
        112,
        file,
        tuple(
            TrimMember(KTrimTypes[slot // 2], edge) for slot, edge in enumerate(path)
        ),
    )
    profile = ProfileWire(
        Feature=ArchiveFeature(31, 19000, 341, Stamp(789, 123)),
        NodeFlags=0x40000000,
        PermanentMarks=(1, 4, 3, 2),
        AxisOrder=(2, 1, 4, 3),
        Poses=(
            SizePose(
                TextWorld=(0.017, -0.003, 0), TextRatio=0.42, WitnessMetres=-0.003
            ),
            SizePose(
                TextWorld=(-0.004, 0.009, 0), TextRatio=0.54, WitnessMetres=-0.004
            ),
        ),
        Draft=draft,
        Restored=False,
        Region=SketchRegionState(114, path),
        DatumTime=121,
        OriginTime=122,
        OriginAccess=123,
        Trim=trim,
    )
    boss = BossWire(
        Feature=ArchiveFeature(32, 19000, 341, Stamp(890, 124)),
        NodeFlags=0x40000140,
        SolidBodyTag=517,
        PartitionMarkId=619,
        ReferenceTime=136,
        CapOrders=(path, (4, 1, 2, 3)),
        Pose=BossPose(
            AnchorSlot=1,
            TangentEdge=1,
            FlipTangent=True,
            Basis=(SpaceVector(1, 0, 0), SpaceVector(0, 0, -1), SpaceVector(0, 1, 0)),
            WitnessMetres=-0.005,
        ),
        Draft=draft,
    )
    return (
        BossIds(Profile=53, Operation=67, Width=23, Height=18, Depth=22),
        profile,
        boss,
    )


# compare independent target identifiers, references and dimensions as passed to the writers
def check_owners(state, ids, profile, boss, width, height, depth, right):
    display = state.Boss.Display
    require(
        (state.Atom.FeatureId, state.Atom.SolidBodyTag, state.Boss.PartitionMarkId)
        == (ids.Operation, boss.SolidBodyTag, boss.PartitionMarkId)
        and state.Boss.Opening.Name == "Pad"
        and state.Profile.Feature.Name == "Construction outline"
        and state.Profile.Feature.TreeId == ids.Profile
        and state.Boss.Opening.Feature == boss.Feature
        and state.Profile.Feature.Feature == profile.Feature,
        "ordinary profile and boss owners from one target allocation",
    )
    require(
        tuple(
            (length.Name, length.Identity, length.Millimetres)
            for length in state.Profile.Lengths
        )
        == (("width_mm", ids.Width, width), ("height_mm", ids.Height, height))
        and (
            display.NameValue,
            display.DimensionId,
            display.DepthMm,
            display.Geometry.Reverse,
        )
        == ("depth_mm", ids.Depth, abs(depth), depth < 0),
        "three independent dimension owners and one signed operation",
    )
    require(
        tuple(
            (line.PermMark, line.CreationId, line.Endpoints, line.RelationCount)
            for line in state.Profile.Lines
        )
        == ((1, 1, (0, 3), 1), (4, 2, (0, 2), 1), (3, 3, (2, 1), 1), (2, 4, (3, 1), 1))
        and tuple(corner.RelationCount for corner in state.Profile.Corners)
        == (3, 0, 1, 1)
        and state.Profile.Attachment.DatumId == (4 if right else 2)
        and state.Profile.Region is profile.Region
        and state.Profile.Trim is profile.Trim
        and state.Profile.AxisOrder == profile.AxisOrder
        and state.Boss.Choice.EdgeOrders == boss.CapOrders
        and state.Boss.Choice.ReferenceTime == boss.ReferenceTime,
        "fresh semantic loop with separately authored traversal and clocks",
    )


# both normal signs are checked on both datums using dimensions outside the source corpus
def hosted_rows():
    ids, profile, boss = wire_state()
    rows = []
    for right, width, height, depth in (
        (False, 37.5, 18.25, 13.5),
        (False, 37.5, 18.25, -8.75),
        (True, 42.25, 17.5, 13.5),
        (True, 42.25, 17.5, -8.75),
    ):
        logical = ProjectBoss(authored_case(right, width, height, depth))
        state = BindBossWriter(logical, ids, profile, boss)
        check_owners(state, ids, profile, boss, width, height, depth, right)
        corners = (0.0, width, height) if right else (width, height, 0.0)
        axial_low, axial_high = min(0.0, depth) / 1000, max(0.0, depth) / 1000
        low = (axial_low, 0.0, 0.0) if right else (0.0, 0.0, axial_low)
        high = (
            (axial_high, width / 1000, height / 1000)
            if right
            else (width / 1000, height / 1000, axial_high)
        )
        signed = (depth, 0.0, 0.0) if right else (0.0, 0.0, depth)
        require(
            (state.Bounds.Minimum, state.Bounds.Maximum, state.DisplacementMm)
            == (low, high, signed),
            "signed world box in metres and displacement in millimetres",
        )
        pose = state.Boss.Display.Geometry
        require(
            (pose.Frame.origin, pose.Normal, pose.Tangent)
            == (
                SpaceVector(*corners),
                SpaceVector(1, 0, 0) if right else SpaceVector(0, 0, 1),
                SpaceVector(0, 0, -1) if right else SpaceVector(-1, 0, 0),
            )
            and tuple(item.Direction for item in state.Profile.Display.Poses)
            == (((0, 1, 0), (-1, 0, 0)) if right else ((1, 0, 0), (0, 1, 0))),
            "bound annotation points and directions use the actual owned edges",
        )
        require(
            state.Boss.Choice.CentreMetres
            == tuple((a + b) / 2 for a, b in zip(low, high, strict=True))
            and isclose(
                state.Boss.Choice.DiameterMetres,
                dist(low, high),
                abs_tol=1e-15,
                rel_tol=0.0,
            ),
            "fresh cap chooser encloses the same world box",
        )
        rows.append((logical.Profile.AxisCode, depth))
    return rows


# a wrongly paired trim configuration, cap loop or dimension binding cannot be reused
def hosted_refusals():
    ids, profile, boss = wire_state()
    logical = ProjectBoss(authored_case(False, 37.5, 18.25, 13.5))
    invalid_file = replace(profile.Trim.File, ConfigName="Other")
    cases = (
        (replace(ids, Operation=ids.Profile), profile, boss, "feature identities"),
        (replace(ids, Height=ids.Width), profile, boss, "dimension identities"),
        (
            ids,
            replace(profile, Trim=replace(profile.Trim, File=invalid_file)),
            boss,
            "same trim configuration",
        ),
        (
            ids,
            profile,
            replace(boss, CapOrders=((1, 3, 2, 4), boss.CapOrders[1])),
            "continuous loop",
        ),
        (
            ids,
            profile,
            replace(boss, Pose=replace(boss.Pose, TangentEdge=12)),
            "annotation corner and edge",
        ),
    )
    for bad_ids, bad_profile, bad_boss, reason in cases:
        try:
            BindBossWriter(logical, bad_ids, bad_profile, bad_boss)
        except ValueError as error:
            require(reason in str(error), f"expected bridge refusal for {reason}")
        else:
            raise ValueError(f"unexpected bridge admission for {reason}")
    return len(cases)


# read the independent pinned geometry and semantic owners without constructing an archive
def native_rows():
    rows = {}
    for _, asset, data, _, measurement in principal_captures():
        name = asset["path"].split("/")[-1]
        if not name.startswith("P03-"):
            continue
        archive = SldprtArchive.from_bytes(data, asset["path"])
        generation = ContainerMo(archive.streams)
        atom = read_atom(archive.require("Contents/Config-0"), generation)
        cursor, profile, _, _, file = open_boss(archive, generation)
        boss = ReadRectBoss(cursor, profile.ObjectIndex, file, atom.ObjectIndex)
        verify_measured(boss, measurement)
        header, logs = ReadHeaderLogs(
            archive.require("Contents/Config-0-ModelHeader"), generation
        )
        ReadHeaderSelf(header, generation)
        saved = ReadHeaderTail(header, generation).Bounds
        measured = measured_bounds(measurement)
        names = {row.TreeId: row.Name for row in logs.Revisions}
        operation = atom.Body.FeatureId
        require(
            operation == boss["native_feature_id"]
            and names[operation] == boss["name"]
            and names[profile.FeatureId] == profile.NameValue,
            "common operation and profile identity in Config, Resolved and ModelHeader",
        )
        require(
            all(
                isclose(a, b, rel_tol=0.0, abs_tol=KFrameTolerance)
                for a, b in zip(
                    (*saved.Minimum, *saved.Maximum),
                    (*measured.Minimum, *measured.Maximum),
                    strict=True,
                )
            ),
            "saved box and independently measured model extents",
        )
        rows[asset["sha256"]] = {
            "variant": name,
            "profile": profile.FeatureId,
            "operation": operation,
            "depth_dimension": boss["depth_display"]["dimension"][
                "native_dimension_id"
            ],
            "bounds_metres": (measured.Minimum, measured.Maximum),
        }
    require(len(rows) == 8, "eight pinned P03 native controls")
    return rows


# hosted and read-only runs share the same intact native evidence authorities
def report(check_bridge):
    rows = native_rows()
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": rows,
        "native_sha256": sha256(
            json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "authored_cases": hosted_rows() if check_bridge else [],
        "refusals": hosted_refusals() if check_bridge else 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify the ordinary boss writer input bridge")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
