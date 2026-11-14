from dataclasses import fields as DataFields
from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Materials.Model.DirectionValue import (
    DirectionValue,
)
from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.FamilyFields import (
    KDirections,
    KMechanicFields,
)
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue


def CheckColor(Color: object) -> None:
    if not isinstance(Color, ColorValue):
        raise ValueError("A typed material RGBA color is required")
    for Channel in (
        Color.RedValue,
        Color.GreenValue,
        Color.BlueValue,
        Color.AlphaValue,
    ):
        if (
            type(CastValue(object, Channel)) not in (int, float)
            or not IsFinite(Channel)
            or not 0 <= Channel <= 1
        ):
            raise ValueError(
                "Material color channels must be finite between zero and one"
            )


def CheckSteps(Steps: object) -> None:
    if not isinstance(Steps, tuple):
        raise ValueError("Material directions must be a short tuple")
    Entries = CastValue(tuple[object, ...], Steps)
    if len(Entries) > 64:
        raise ValueError("Material directions must be a short tuple")
    Visited: set[tuple[str, str]] = set()
    for Entry in Entries:
        if (
            type(Entry) is not DirectionValue
            or Entry.FieldKey not in KMechanicFields
            or Entry.Direction not in KDirections
            or (Entry.FieldKey, Entry.Direction) in Visited
        ):
            raise ValueError("Material direction is unknown or repeated")
        if type(CastValue(object, Entry.Value)) not in (int, float) or not IsFinite(
            Entry.Value
        ):
            raise ValueError("Material part values must be finite numbers")
        Visited.add((Entry.FieldKey, Entry.Direction))


def CheckParts(Value: object, PartType: type[object]) -> None:
    if type(Value) is not PartType:
        raise ValueError("Material part specification has the wrong type")
    for Field in DataFields(CastValue(type, PartType)):
        Entry: object = getattr(Value, Field.name)
        Declared = str(Field.type)
        if Entry is None:
            continue
        if "DirectionValue" in Declared:
            CheckSteps(Entry)
        elif "ColorValue" in Declared:
            CheckColor(Entry)
        elif "bool" in Declared:
            if type(Entry) is not bool:
                raise ValueError("Material part flag must be a boolean")
        elif "str" in Declared:
            if not isinstance(Entry, str) or not Entry or len(Entry) > 1024:
                raise ValueError("Material part name must be short nonempty text")
            if "\x00" in Entry:
                raise ValueError("Material part name must not contain NUL")
        elif "int" in Declared and "float" not in Declared:
            if type(Entry) is not int:
                raise ValueError("Material part choice must be an integer")
        elif type(Entry) not in (int, float) or not IsFinite(CastValue(float, Entry)):
            raise ValueError("Material part values must be finite numbers")
