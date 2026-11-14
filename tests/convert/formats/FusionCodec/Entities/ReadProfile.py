from json import loads as LoadJson
from lzma import decompress as Decompress
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from tests.convert.formats.FusionCodec.Entities.ProfileJson import ProfileJson
from tests.convert.formats.FusionCodec.Entities.ReadWire import ReadWire

KProfilePath = (
    FilePath(__file__).resolve().parents[5]
    / "re/Fusion/Reconstruction/EntityGraph/DesignProfile.json.xz"
)


def ReadProfile(Targets: tuple[ExternalTarget, ...]) -> EntityProfile:
    Value = CastValue(ProfileJson, LoadJson(Decompress(KProfilePath.read_bytes())))
    assert Value["ExternalTargets"] == []
    Classes = tuple(
        ClassSchema(
            Entry["ClassGuid"],
            Entry["BaseGuid"],
            Entry["SchemaVersion"],
            tuple(
                FieldSpec(
                    Field["FieldName"], ReadWire(Field["ValueType"]), Field["IsSaved"]
                )
                for Field in Entry["Members"]
            ),
            Entry["IsValue"],
        )
        for Entry in Value["Classes"]
    )
    return EntityProfile(Value["RootGuid"], Classes, Targets)
