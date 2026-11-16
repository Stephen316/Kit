# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from base64 import b64decode as DecodeRef
from pathlib import Path as FilePath
from struct import pack as PackValue

from PairedCaptureIntake import require as RequirePad, sha256 as ShaValue

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.PlaneBasis import KUnitRows
from convert.adapters.solidworks.Resolved.FaceIdentity import (
    KCapClass,
    KEdgeClass,
    SurfaceKey,
)
from convert.adapters.solidworks.Resolved.TwoPad.PadHistory import (
    PadHistory,
    ReadPadHistory,
)
from convert.api.ApiOpen import OpenDocument
from interchange.document.Models.DocumentModel import CadDocument

from PadGeometry import KSavedPhases, CheckVector
from PadReceipts import ReadPadBytes


# an independently measured persistent reference must name the reached cap and edges in order
def CheckNativeRef(Reference: str, Proof: PadHistory) -> None:
    DataValue = DecodeRef(Reference, validate=True)
    FaceValue = Proof.Support["face"]["component"]["occurrence"]
    Primary = PackValue("<iIi", *SurfaceKey(FaceValue["primary"])[1:])
    Edges = tuple(
        PackValue("<iIi", *SurfaceKey(Value)[1:])
        for Value in FaceValue["ordered_edges"]
    )
    CapTag, EdgeTag = KCapClass.encode(), KEdgeClass.encode()
    RequirePad(
        DataValue.count(CapTag) == DataValue.count(EdgeTag) == 1,
        "Unexpected native cap and side reference classes",
    )
    CapStart, EdgeStart = DataValue.index(CapTag), DataValue.index(EdgeTag)
    RequirePad(
        CapStart < EdgeStart and DataValue[CapStart:EdgeStart].count(Primary) == 1,
        "Native reference does not resolve the typed base cap",
    )
    TailValue = DataValue[EdgeStart:]
    RequirePad(
        all(TailValue.count(Value) == 1 for Value in Edges),
        "Missing or repeated persistent side occurrence",
    )
    Locations = tuple(TailValue.index(Value) for Value in Edges)
    RequirePad(
        Locations == tuple(sorted(Locations)),
        "Persistent side order differs from the typed cap",
    )


# the independently observed sketch pose must agree with the complete typed archive walk
def CheckReadback(CaseValue: dict, Proof: PadHistory) -> None:
    Frame = Proof.Support["face"]["plane"]
    PoseValue = Frame["transform"]
    Basis = PoseValue["basis"] if PoseValue["basis"] is not None else KUnitRows
    Transform = (*Basis, *PoseValue["translation_scale"], 0, 0, 0)
    RequirePad(
        (
            Proof.BaseValue["name"],
            Proof.UpperProfile.NameValue,
            Proof.UpperValue["name"],
        )
        == ("BaseBoss", "UpperSketch", "UpperBoss"),
        "Typed archive owner names differ from their native records",
    )
    TopDepth = Proof.UpperValue["end_specification"]["depth_display"]
    RequirePad(
        TopDepth is not None
        and Proof.BaseEnd["depth_display"]["dimension"]["metres"] * 1000
        == CaseValue["base_depth_mm"]
        and TopDepth["dimension"]["metres"] * 1000 == CaseValue["upper_depth_mm"],
        "Typed archive depths differ from native saved measurements",
    )
    for Stage in KSavedPhases:
        Snapshot = CaseValue[Stage]
        Support = Snapshot["upper_support"]
        CheckNativeRef(Support["reference"], Proof)
        CheckVector(
            Support["origin_world_mm"],
            tuple(Value * 1000 for Value in Frame["root_metres"]),
            "saved support point",
        )
        CheckVector(
            Support["normal_world"], Frame["normal_world"], "saved support normal"
        )
        UpperSketch = next(
            Value
            for Value in Snapshot["sketches"]
            if Value["name"] == Proof.UpperProfile.NameValue
        )
        CheckVector(
            UpperSketch["model_to_sketch_transform"],
            Transform,
            "saved model to sketch transform",
        )


# the public strict read and neutral JSON must preserve the same selected face and dependency
def CheckSdkRound(DataValue: bytes, Proof: PadHistory) -> str:
    Document = OpenDocument(
        DataValue, SourceFormat="solidworks.sldprt", StrictMode=True
    )
    (Upper,) = (
        Value
        for Value in Document.sketches
        if Value.name == Proof.UpperProfile.NameValue
    )
    (Plane,) = (
        Value for Value in Document.support_planes if Value.id == Upper.support_plane_id
    )
    (FacePick,) = (
        Value for Value in Document.selections if Value.id == Plane.support_selection_id
    )
    Producer = Proof.BaseValue["native_feature_id"]
    Occurrences = tuple(
        Value["occurrence"]
        for Value in Proof.Support["face"]["component"]["occurrence"]["ordered_edges"]
    )
    BossId = f"sldprt:feature:{Producer}"
    ProfileId = f"sldprt:feature:{Proof.UpperProfile.FeatureId}"
    (Feature,) = (Value for Value in Document.feature_timeline if Value.id == ProfileId)
    RequirePad(
        Upper.attributes.get("support_plane_source") == "typed-archive-face"
        and Feature.sketch_id == Upper.id
        and Feature.input_feature_ids == (BossId,)
        and FacePick.query.get("native_source_id") == Producer
        and FacePick.query.get("native_occurrence") == 1
        and tuple(FacePick.query.get("native_ordered_edge_occurrences", ()))
        == Occurrences
        and len(Document.bodies) == 1
        and Document.bodies[0].final_feature_id
        == f"sldprt:feature:{Proof.UpperValue['native_feature_id']}",
        "Public SDK does not retain the verified face and boss ownership",
    )
    Origin = Plane.transform.origin
    CheckVector(
        [Origin.x, Origin.y, Origin.z],
        tuple(Value * 1000 for Value in Proof.Support["face"]["plane"]["root_metres"]),
        "public face plane origin",
    )
    Normal = Plane.transform.z_axis
    CheckVector(
        [Normal.x, Normal.y, Normal.z],
        Proof.Support["face"]["plane"]["normal_world"],
        "public face plane normal",
    )
    Encoded = Document.to_json()
    Restored = CadDocument.from_json(Encoded)
    Restored.assert_valid()
    RequirePad(
        Restored.to_json() == Encoded,
        "Neutral JSON round trip changed the public result",
    )
    return ShaValue(Encoded.encode("utf-8"))


# a case can contribute evidence only after its receipt and licensed archive agree
def CheckPadArchive(Directory: FilePath, CaseValue: dict, StrictSdk: bool) -> dict:
    SaveValue = CaseValue["save"]
    FileName = f"{CaseValue['variant']}.SLDPRT"
    RequirePad(
        SaveValue["file"] == FileName
        and SaveValue["save_errors"] == SaveValue["save_warnings"] == 0,
        f"Unproved native save: {FileName}",
    )
    Digest = SaveValue["sha256"]
    DataValue = ReadPadBytes(Directory, FileName, Digest)
    RequirePad(
        len(DataValue) == SaveValue["size_bytes"], f"Archive size changed: {FileName}"
    )
    Archive = SldprtArchive.from_bytes(DataValue)
    RequirePad(
        ContainerMo(Archive.streams) == KConfigGen,
        "Unexpected modern SOLIDWORKS archive generation",
    )
    Proof = ReadPadHistory(
        Archive.require("Contents/Config-0"),
        Archive.require("Contents/Config-0-ResolvedFeatures"),
    )
    CheckReadback(CaseValue, Proof)
    Observed = CaseValue["before_rebuild"]
    RowValue = {
        "variant": CaseValue["variant"],
        "archive_sha256": Digest,
        "volume_mm3": Observed["volume_mm3"],
        "centroid_mm": Observed["center_of_mass_mm"],
        "upper_support_mm": Observed["upper_support"]["origin_world_mm"],
        "base_depth_mm": CaseValue["base_depth_mm"],
        "upper_depth_mm": CaseValue["upper_depth_mm"],
    }
    if StrictSdk:
        RowValue["neutral_json_sha256"] = CheckSdkRound(DataValue, Proof)
    return RowValue
