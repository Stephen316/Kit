from convert.formats.Fusion.DrawingCodec.Members.JsonFields import (
    JsonFields,
    KFrozenJson,
)


# the setting item contract needs a shared interpretation so sheet objects retain their intended document relationships
def SettingItem(Ident: str, Value: KFrozenJson) -> JsonFields:
    return JsonFields((("Id", Ident), ("Value", Value)))


# the setting version contract needs a shared interpretation so sheet objects retain their intended document relationships
def SettingVersion(Number: int) -> JsonFields:
    return JsonFields((("Version", Number),))
