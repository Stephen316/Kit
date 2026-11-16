from json import loads as LoadJson
from lzma import decompress as Decompress
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile
from convert.Formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.Formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from tests.Convert.Formats.FusionCodec.Entities.ProfileJson import ProfileJson
from tests.Convert.Formats.FusionCodec.Entities.ReadWire import ReadWire

# profile path needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KProfilePath = (
    FilePath(__file__).resolve().parents[5]
    / "re/Fusion/Reconstruction/EntityGraph/DesignProfile.json.xz"
)


# shared read profile setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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
