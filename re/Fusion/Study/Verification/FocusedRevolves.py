#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Reproduce scoped saved-file checks for three Fusion feature families."""

from argparse import ArgumentParser
from dataclasses import replace
from functools import partial as Partial
from math import atan2, cos, isclose, pi, radians, sin
from pathlib import Path
import zipfile as ZipModule
from RevolvePlanes.PlaneIntervals import PlaneBranches, SelectPlaneSpan

from asm_records import inspect_asm
from decode_basics import attach_parameters, decode_basics, named_features
from decode_brep import decode_topology
from decode_parameters import decode_stream
from decode_plane_extrusion_reconstruction import decode_plane_extrusion_reconstruction
from decode_shell_reconstruction import decode_shell_reconstruction
from discover_features import discover_features
from fusion_archive import _decompress_zstd as InflateZstd, read_members
from fusion_metadata import design_records
from validate_plane_extrusion_reconstruction_integration import FILES as ExtrudeFiles
from validate_shell_reconstruction_integration import FILES as ShellFiles


# comparison on fixed inventories covers accepted shapes and empty controls
def CheckFocused(Files, Decode, Summary, ZstdLibrary):
    Count = 0
    for Filename in Files:
        FilePath = Path(Filename)
        (Stream,) = decode_basics(FilePath, ZstdLibrary)["streams"]
        Member = Stream["member"]
        Metadata = Member.removesuffix("BulkStream.dat") + "MetaStream.dat"
        Members = read_members(
            FilePath,
            ZstdLibrary,
            MemberSuffixes=(Member, Metadata, ".smb", ".smbh"),
        )
        BulkData = Members[Member]
        Records, Index = design_records(BulkData, Members[Metadata])
        Features = named_features(BulkData, Records)
        discover_features(BulkData, Records, Features, Index)
        Params, _ = decode_stream(BulkData, Records)
        attach_parameters(BulkData, Records, Features, Params)
        Result = Decode(
            BulkData, Records, Features, Member, Members, Stream["body_blob_bindings"]
        )
        if Summary in Stream:
            assert Result == Stream[Summary], Filename
        else:
            assert not Result["decoded"] and not Result["unresolved"], Filename
        Count += len(Result["decoded"])
    return Count


# independent edge evaluation checks the physical sector even across angle wrapping
def CheckArcs(Parsed, Graph, Start, Finish):
    Records = Parsed["records"]
    Count = 0
    for EdgeIndex in Graph["edge_indices"]:
        Edge = Records[EdgeIndex]["tokens"]
        CurveIndex = Edge[8]["value"]
        assert CurveIndex >= 0
        Curve = Records[CurveIndex]
        if Curve["name"] != "ellipse-curve":
            continue
        NormalX, NormalY, NormalZ = Curve["tokens"][4]["value"]
        RefX, RefY, RefZ = Curve["tokens"][5]["value"]
        assert abs(NormalX) + abs(NormalZ) + abs(RefY) < 1e-9
        assert isclose(abs(NormalY), 1.0, abs_tol=1e-9)
        assert Curve["tokens"][6]["value"] == 1.0
        Lower, Upper = Edge[4]["value"], Edge[6]["value"]
        Middle = (Lower + Upper) / 2
        RadialX = cos(Middle) * RefX + sin(Middle) * NormalY * RefZ
        RadialZ = cos(Middle) * RefZ - sin(Middle) * NormalY * RefX
        Phase = atan2(RadialZ, RadialX)
        Offset = (Phase - (Start + Finish) / 2 + pi) % (2 * pi) - pi
        assert isclose(abs(Upper - Lower), Finish - Start, abs_tol=1e-9)
        assert abs(Offset) < 1e-9
        Count += 1
    assert Count == 4


# saved reference sectors verify the decoder without sharing the source branch computation
def CheckRevolves(ZstdLibrary, CheckKit=False):
    Capture = Path("revolveto-b1d196f65c46")
    for Name, Degrees, PlaneCount in (
        ("negative_plane", (0, 35), 1),
        ("positive_plane", (0, 135), 1),
        ("two_planes", (135, 215), 2),
    ):
        FilePath = Capture / (Name + ".f3d")
        Original = decode_basics(FilePath, ZstdLibrary)
        Result = decode_basics(FilePath, ZstdLibrary, AllowPlaneLimits=True)
        (Stream,) = Result["streams"]
        Summary = Stream["revolve_reconstruction"]
        assert not Summary["unresolved"], (Name, Summary["unresolved"])
        (Reconstruction,) = Summary["decoded"]
        Evidence = Reconstruction["plane_limit_evidence"]
        assert len(Evidence["source_plane_radial_roots_radians"]) == PlaneCount, Name
        Expected = tuple(map(radians, Degrees))
        for Angle, Target in zip(
            Evidence["source_directed_interval_radians"], Expected
        ):
            assert isclose(Angle, Target, abs_tol=1e-9), Name
        Proof = Reconstruction["native_cache_geometry_corroboration"]
        assert Proof["complete_bundle_residual_raw"] < 1e-8, Name
        Cache = Reconstruction["history_blob_member"]
        Parsed = inspect_asm(
            read_members(FilePath, ZstdLibrary, MemberSuffixes=(Cache,))[Cache]
        )
        (Graph,) = (
            Graph
            for Graph in decode_topology(Parsed)["body_graphs"]
            if Graph["body_index"] == Reconstruction["asm_body_index"]
        )
        assert Graph["counts"] == Proof["counts"], Name
        CheckArcs(Parsed, Graph, *Expected)
        (Feature,) = (
            Feature for Feature in Stream["features"] if Feature["kind"] == "Revolve"
        )
        if CheckKit:
            CheckKitRev(
                FilePath, ZstdLibrary, Feature, Parsed, Graph, Expected, Reconstruction
            )
        assert Feature.pop("revolve_reconstruction") == Reconstruction
        Stream["revolve_reconstruction"] = Original["streams"][0][
            "revolve_reconstruction"
        ]
        assert Result == Original, Name


# the sdk definition must survive json and match independently evaluated cache arcs
def CheckKitRev(
    FilePath, ZstdLibrary, NativeFeature, Parsed, Graph, Expected, Reconstruction
):
    from convert.formats.Fusion.DocumentRead import ReadFusionDoc
    from interchange.document.models.DocumentModel import CadDocument
    from interchange.features.FeaturePlaneRev import PlaneRevolve

    Codec = None
    if ZstdLibrary is not None or not hasattr(ZipModule, "ZIP_ZSTANDARD"):
        Codec = Partial(InflateZstd, library_path=ZstdLibrary)
    Document = ReadFusionDoc(FilePath, InflateZstd=Codec)
    assert CadDocument.from_json(Document.to_json()) == Document
    CheckKitBody(Document, Graph, Reconstruction)
    (StepValue,) = (
        Value for Value in Document.feature_timeline if Value.kind.value == "revolution"
    )
    Definition = StepValue.definition
    assert isinstance(Definition, PlaneRevolve)
    Actual = Definition.StartRadians, Definition.EndRadians
    assert all(
        isclose(Value, Target, abs_tol=1e-9) for Value, Target in zip(Actual, Expected)
    )
    CheckArcs(Parsed, Graph, *Actual)
    Selections = {Value.id: Value for Value in Document.selections}
    Controls = NativeFeature["revolve"]
    assert (
        int(Selections[Definition.AxisSelectionId].provenance.native_id)
        == Controls["axis_selection_record_object_id"]
    )
    assert tuple(
        int(Selections[Identity].provenance.native_id)
        for Identity in Definition.PlaneSelectionIds
    ) == tuple(
        Controls[Side]["selection_record_object_id"]
        for Side in ("side_one", "side_two")
        if Side in Controls
    )


# the neutral body must match the mapped result without reusing cached topology
def CheckKitBody(Document, Graph, Reconstruction):
    (Body,) = Document.bodies
    Model = Document.brep
    assert Model is not None and not Model.GetErrors(frozenset((Body.id,)))
    (BrepBody,) = Model.bodies
    assert BrepBody.design_body_id == Body.id
    assert (
        int(Body.provenance.native_id) == Reconstruction["source_native_body_object_id"]
    )
    assert Body.attributes["fusion.geometry_source"] == "source_profile_revolve"
    for NameValue in ("vertex", "edge", "face", "shell"):
        assert (
            getattr(Body.topology, f"{NameValue}_count") == Graph["counts"][NameValue]
        )
    Source = Reconstruction["derived_geometry"]
    assert isclose(Body.topology.volume, Source["volume_cm3"] * 1000, rel_tol=1e-9)
    assert isclose(
        Body.topology.surface_area, Source["surface_area_cm2"] * 100, rel_tol=1e-9
    )
    Bounds = Body.topology.bounding_box
    for BoundName in ("minimum", "maximum"):
        Position = getattr(Bounds, BoundName)
        Expected = Source["component_axis_aligned_bounds_cm"][BoundName]
        assert all(
            isclose(Value, Target * 10, rel_tol=1e-9, abs_tol=1e-8)
            for Value, Target in zip((Position.x, Position.y, Position.z), Expected)
        )


# oracle sectors exercise target order and branches beyond the tracked fixtures
def CheckPlaneRule():
    for Angles, Sector in (
        ((20, 45), (160, 315)),
        ((-35, -70), (70, 215)),
        ((15, -65), (165, 245)),
        ((80, -20), (100, 200)),
        ((15,), (0, 165)),
        ((-65,), (0, 65)),
    ):
        Roots = []
        for Angle in map(radians, Angles):
            Roots.append(
                PlaneBranches(
                    (0, 0, 0),
                    (sin(Angle), 0, cos(Angle)),
                    (0, 0, 0),
                    (0, -1, 0),
                    (1, 0, 0),
                    (0, 0, 1),
                )
            )
        Expected = tuple(map(radians, Sector))
        for Order in (Roots, list(reversed(Roots))):
            for Actual, Target in zip(SelectPlaneSpan(Order), Expected):
                assert isclose(Actual, Target, abs_tol=1e-9), Angles


# a captured legacy record exercises the observed extension and rejects unknown bytes
def CheckParamLayout(ZstdLibrary):
    Source = Path("revolveto-b1d196f65c46/positive_plane.f3d")
    Members = read_members(
        Source, ZstdLibrary, MemberSuffixes=("/BulkStream.dat", "/MetaStream.dat")
    )
    (Member,) = (
        Name
        for Name in Members
        if Name.endswith("/FusionDesignSegmentType1/BulkStream.dat")
    )
    Data = Members[Member]
    Records, _ = design_records(
        Data, Members[Member.replace("BulkStream", "MetaStream")]
    )
    Parameters, _ = decode_stream(Data, Records)
    (Angle,) = (Param for Param in Parameters if Param["role"] == "AlongAngle")
    (Record,) = (
        Entry
        for Entry in Records
        if Entry.is_primary and Entry.object_id == Angle["parameter_object_id"]
    )
    RoleOffset = Angle["role_offset"]
    Extended = replace(Record, end=Record.end + 1)
    for ByteValue in (b"\0", b"\x01"):
        Modified = Data[:RoleOffset] + ByteValue + Data[RoleOffset:]
        Decoded, Rejected = decode_stream(Modified, (Extended,))
        if ByteValue == b"\0":
            assert not Rejected
            assert Decoded == [
                dict(
                    Angle,
                    role_offset=RoleOffset + 1,
                    value_offset=Angle["value_offset"] + 1,
                    expression_metadata_hex=Angle["expression_metadata_hex"] + "00",
                )
            ]
        else:
            assert not Decoded and len(Rejected) == 1


if __name__ == "__main__":
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--zstd-library")
    Parser.add_argument("--kit", action="store_true")
    Options = Parser.parse_args()
    CheckPlaneRule()
    CheckParamLayout(Options.zstd_library)
    CheckRevolves(Options.zstd_library, Options.kit)
    assert (
        CheckFocused(
            ShellFiles,
            decode_shell_reconstruction,
            "shell_reconstruction",
            Options.zstd_library,
        )
        == 13
    )
    assert (
        CheckFocused(
            ExtrudeFiles,
            decode_plane_extrusion_reconstruction,
            "plane_extrusion_reconstruction",
            Options.zstd_library,
        )
        == 3
    )
    print(
        "Verified 3 plane-limited Revolves, 15 Shell fixtures and 8 Extrude fixtures."
    )
    if Options.kit:
        print("Verified Kit definitions, solids and JSON for the 3 tracked Revolves.")
