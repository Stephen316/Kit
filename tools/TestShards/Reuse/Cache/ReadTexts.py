from __future__ import annotations

from tools.TestShards.Reuse.Cache.ReadObject import ReadObject


def ReadTexts(Value: object, Label: str) -> dict[str, str]:
    Fields = ReadObject(Value, Label)
    Texts = {
        FieldKey: Member
        for FieldKey, Member in Fields.items()
        if isinstance(Member, str)
    }
    if len(Texts) != len(Fields):
        raise ValueError(f"{Label} has a value that is not text")
    return Texts
