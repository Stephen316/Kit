from dataclasses import fields as DataFields
from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase
from typing import Protocol, cast as CastValue

from convert.adapters.Fusion.State.StateTypes import KStateNames
from convert.formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import (
    MechanicSpec,
)


# the record maker contract needs a dedicated boundary so public document claims remain grounded in native records
class RecordMaker(Protocol):

    # record maker needs an explicit validity boundary so public document claims remain grounded in native records
    def __call__(self, **Values: object) -> object:
        raise TypeError("a concrete semantic-state constructor is required")


# the record operation needs a distinct decoding boundary so public document claims remain grounded in native records
def DecodeRecord(NameValue: object, Values: dict[str, object]) -> object:
    if not isinstance(NameValue, str) or NameValue not in KStateNames:
        raise ValueError("Unknown Fusion semantic-state record")
    ClassType = KStateNames[NameValue]
    if (
        NameValue
        == "convert.formats.Fusion.DocumentCodec.Model.DocumentModel.DocumentModel"
    ):
        Values = {"Meshes": (), "Forms": (), **Values}
    if (
        NameValue
        == "convert.formats.Fusion.DocumentCodec.Model.ParsedSegment.ParsedSegment"
    ):
        Values = {"BulkSlack": b"", **Values}
    if (
        NameValue
        == "convert.formats.Fusion.GraphicsCodec.Model.Nodes.SketchWorld.SketchWorld"
    ):
        Values = {"RegularNodes": (), "NoCullingNodes": (), **Values}
    if (
        NameValue
        == "convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec.MaterialSpec"
    ):
        Values = {
            "ClassName": "Generic",
            "Mechanics": MechanicSpec(),
            "Thermal": None,
            "Finish": FinishSpec(),
            "TypeName": None,
            **Values,
        }
    if not IsDataClass(ClassType) or set(Values) != {
        Field.name for Field in DataFields(ClassType)
    }:
        raise ValueError("Fusion semantic-state record fields disagree")
    return CastValue(RecordMaker, ClassType)(**Values)


# the enum operation needs a distinct decoding boundary so public document claims remain grounded in native records
def DecodeEnum(NameValue: object, Value: object) -> object:
    if not isinstance(NameValue, str) or NameValue not in KStateNames:
        raise ValueError("Unknown Fusion semantic-state enum")
    ClassType = KStateNames[NameValue]
    if not issubclass(ClassType, EnumBase):
        raise ValueError("Fusion semantic-state enum type disagrees")
    return ClassType(Value)
