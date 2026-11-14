from convert.formats.Fusion.DrawingCodec.Members.JsonFields import (
    JsonFields,
    KFrozenJson,
)


def SettingItem(Ident: str, Value: KFrozenJson) -> JsonFields:
    return JsonFields((("Id", Ident), ("Value", Value)))


def SettingVersion(Number: int) -> JsonFields:
    return JsonFields((("Version", Number),))
