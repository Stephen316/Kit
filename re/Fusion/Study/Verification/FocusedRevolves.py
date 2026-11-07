# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Reproduce scoped saved-file checks for three Fusion feature families."""

from argparse import ArgumentParser
from math import atan2, cos, isclose, pi, radians, sin
from pathlib import Path

from asm_records import inspect_asm
from decode_basics import attach_parameters, decode_basics, named_features
from decode_brep import decode_topology
from decode_parameters import decode_stream
from decode_plane_extrusion_reconstruction import decode_plane_extrusion_reconstruction
from decode_shell_reconstruction import decode_shell_reconstruction
from discover_features import discover_features
from fusion_archive import read_members
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


# saved reference sectors verify the decoder independently of its candidate matcher
def CheckRevolves(ZstdLibrary):
    Capture = Path("revolveto-b1d196f65c46")
    for Name, Degrees, Candidates in (
        ("negative_plane", (0, 35), 4),
        ("positive_plane", (0, 135), 4),
        ("two_planes", (135, 215), 8),
    ):
        FilePath = Capture / (Name + ".f3d")
        Original = decode_basics(FilePath, ZstdLibrary)
        Result = decode_basics(FilePath, ZstdLibrary, AllowPlaneLimits=True)
        (Stream,) = Result["streams"]
        Summary = Stream["revolve_reconstruction"]
        assert not Summary["unresolved"], (Name, Summary["unresolved"])
        (Reconstruction,) = Summary["decoded"]
        Evidence = Reconstruction["plane_limit_evidence"]
        assert Evidence["candidate_count"] == Candidates, Name
        Expected = tuple(map(radians, Degrees))
        for Angle, Target in zip(
            Evidence["matched_directed_interval_radians"], Expected
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
        assert Feature.pop("revolve_reconstruction") == Reconstruction
        Stream["revolve_reconstruction"] = Original["streams"][0][
            "revolve_reconstruction"
        ]
        assert Result == Original, Name


if __name__ == "__main__":
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--zstd-library")
    Options = Parser.parse_args()
    CheckRevolves(Options.zstd_library)
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
