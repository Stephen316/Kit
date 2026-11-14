from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshLayout import (
    KBodyGuid,
    KGeometryGuid,
)
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)
from tests.convert.formats.FusionCodec.Documents.Mesh.AlterMeshField import (
    AlterMeshField,
)


def AlterMeshGraph(Segment: ParsedSegment, Variant: str) -> ParsedSegment:
    Owners = tuple(
        Record for Record in Segment.Records if Record.IsPrimary and Record.Groups
    )
    Geometries = tuple(
        Record
        for Record in Owners
        if Record.Groups[0].ClassGuid.upper() == KGeometryGuid
    )
    assert len(Geometries) > 1
    Selected = Geometries[0]
    if Variant == "reciprocal":
        Replacement = AlterMeshField(
            Selected,
            "rSerializerTrigger",
            GroupFields(Geometries[1].Groups)["rSerializerTrigger"],
        )
    elif Variant == "stale":
        Replacement = AlterMeshField(Selected, "needsUpdate", True)
    elif Variant == "body":
        Selected = next(
            Record
            for Record in Owners
            if Record.Groups[0].ClassGuid.upper() == KBodyGuid
        )
        Replacement = AlterMeshField(Selected, "rMeshGeometry", None)
    else:
        raise ValueError("Unknown mesh graph mutation")
    return ReplaceValue(
        Segment,
        Records=tuple(
            Replacement if Record is Selected else Record for Record in Segment.Records
        ),
    )
